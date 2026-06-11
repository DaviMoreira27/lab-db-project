import csv
import logging
import time
from datetime import date
 
import asyncpg
 
from app.database.database_service import get_pool
from app.modulos.user_logging import registrar_criar_piloto
 
logger = logging.getLogger(__name__)
 
 
def _log_query(label: str, elapsed_s: float) -> None:
    logger.debug("[query] %s | %.1f ms", label, elapsed_s * 1000)
 
 
async def buscar_dados_dashboard_escuderia(constructor_id: int) -> asyncpg.Record | None:
    # Chama a função get_constructor_dashboard, que já devolve numa linha só o
    # nome, a contagem de pilotos, as vitórias e o primeiro/último ano.
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        dados = await conexao.fetchrow(
            "SELECT * FROM get_constructor_dashboard($1)",
            constructor_id,
        )
        _log_query("(funcao)get_constructor_dashboard", time.perf_counter() - t)
        return dados
 
 
async def consultar_piloto_por_sobrenome(
    constructor_id: int, sobrenome: str
) -> list[asyncpg.Record]:
    # Procura pilotos com aquele sobrenome que JÁ CORRERAM pela escuderia
    # logada. O vínculo "correu pela escuderia" vem da tabela results, como o
    # enunciado sugere. DISTINCT porque o mesmo piloto tem várias linhas em
    # results (uma por corrida).
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        result = await conexao.fetch(
            "SELECT DISTINCT"
            "  d.given_name || ' ' || d.family_name AS piloto,"
            "  d.date_of_birth AS data_nascimento,"
            "  co.name AS pais"
            " FROM results res"
            " JOIN drivers d ON d.id = res.driver_id"
            " JOIN countries co ON co.id = d.country_id"
            " WHERE res.constructor_id = $1"
            "   AND LOWER(d.family_name) = LOWER($2)"
            " ORDER BY piloto",
            constructor_id,
            sobrenome,
        )
        _log_query("(query)consultar_piloto_por_sobrenome", time.perf_counter() - t)
        return result
 
 
def _parsear_linha(linha: list[str]) -> tuple[str, str, str, date, int]:
    # Cada linha do arquivo é: driver_ref, given_name, family_name,
    # date_of_birth (YYYY-MM-DD), country_id. Qualquer linha fora desse formato
    # vira um erro que a gente reporta sem derrubar o resto.
    if len(linha) != 5:
        raise ValueError(f"esperava 5 campos, veio {len(linha)}")
 
    driver_ref, given_name, family_name, data_str, country_str = (
        campo.strip() for campo in linha
    )
    if not driver_ref or not given_name or not family_name:
        raise ValueError("driver_ref, nome e sobrenome são obrigatórios")
 
    nascimento = date.fromisoformat(data_str)
    country_id = int(country_str)
    return driver_ref, given_name, family_name, nascimento, country_id
 
 
async def inserir_pilotos_por_arquivo(userid: int, caminho: str) -> dict:
    # Lê um CSV sem cabeçalho, uma linha por piloto. 
    # Para cada um, confere se
    # já não existe alguém com o mesmo nome e sobrenome (checagem global, é o
    # que o enunciado pede). 
    
    # Se existir, pula e avisa
    # se não, insere em drivers e a trigger sync_driver_to_users cria o usuário sozinha
    
    # não criamos vínculo explícito do piloto novo com a escuderia logada. 
    # No nosso esquema a associação piloto/escuderia só existe através de results, 
    # e um piloto recém-cadastrado ainda não tem corrida nenhuma
    # então ele entra só em drivers. 
    # Isso esta documentado no relatório.
    
    # Cada piloto vai na sua própria transação, 
    # então um erro numa linha (um driver_ref repetido, por exemplo) não cancela os outros que deram certo
    inseridos: list[str] = []
    duplicados: list[str] = []
    erros: list[str] = []
 
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        linhas = list(csv.reader(arquivo))
 
    pool = get_pool()
    async with pool.acquire() as conexao:
        for numero, linha in enumerate(linhas, start=1):
            if not linha or all(not campo.strip() for campo in linha):
                continue  # ignora linha em branco
 
            try:
                driver_ref, given_name, family_name, nascimento, country_id = (
                    _parsear_linha(linha)
                )
            except ValueError as e:
                erros.append(f"linha {numero}: {e}")
                continue
 
            nome_completo = f"{given_name} {family_name}"
 
            ja_existe = await conexao.fetchval(
                "SELECT 1 FROM drivers"
                " WHERE LOWER(given_name) = LOWER($1)"
                "   AND LOWER(family_name) = LOWER($2)",
                given_name,
                family_name,
            )
            if ja_existe:
                duplicados.append(nome_completo)
                continue
 
            try:
                async with conexao.transaction():
                    t = time.perf_counter()
                    await conexao.execute(
                        "INSERT INTO drivers"
                        " (driver_ref, given_name, family_name, date_of_birth, country_id)"
                        " VALUES ($1, $2, $3, $4, $5)",
                        driver_ref,
                        given_name,
                        family_name,
                        nascimento,
                        country_id,
                    )
                    await registrar_criar_piloto(userid, conexao)
                    _log_query("(insert)inserir_piloto_arquivo", time.perf_counter() - t)
                inseridos.append(nome_completo)
            except asyncpg.PostgresError as e:
                # A trigger pode barrar se o login gerado já existir, ou o
                # driver_ref pode estar repetido. Reporta e segue.
                erros.append(f"linha {numero} ({nome_completo}): {e}")
 
    return {
        "inseridos": inseridos,
        "duplicados": duplicados,
        "erros": erros,
    }
 
 
async def buscar_relatorio_pilotos_vitorias(constructor_id: int) -> list[asyncpg.Record]:
    # Relatório 4 chama a função get_constructor_drivers_wins
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        result = await conexao.fetch(
            "SELECT * FROM get_constructor_drivers_wins($1)",
            constructor_id,
        )
        _log_query("(funcao)get_constructor_drivers_wins", time.perf_counter() - t)
        return result
 
 
async def buscar_relatorio_status_escuderia(constructor_id: int) -> list[asyncpg.Record]:
    # Relatório 5 chama a função get_constructor_status_count
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        result = await conexao.fetch(
            "SELECT * FROM get_constructor_status_count($1)",
            constructor_id,
        )
        _log_query("(funcao)get_constructor_status_count", time.perf_counter() - t)
        return result
 
