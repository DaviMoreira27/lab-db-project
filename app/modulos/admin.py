import asyncpg
from datetime import date

from app.database.database_service import get_pool
from app.modulos.user_logging import registrar_criar_escuderia, registrar_criar_piloto


async def buscar_dados_dashboard() -> dict:
    pool = get_pool()
    async with pool.acquire() as conexao:
        totais = await conexao.fetchrow(
            "SELECT"
            " (SELECT COUNT(*) FROM drivers) AS pilotos,"
            " (SELECT COUNT(*) FROM constructors) AS escuderias,"
            " (SELECT COUNT(*) FROM seasons) AS temporadas,"
            " (SELECT MAX(year) FROM seasons) AS ano_temporada_recente"
        )
        corridas = await conexao.fetch("SELECT * FROM vw_corridas_temporada_atual")
        escuderias = await conexao.fetch("SELECT * FROM vw_escuderias_temporada_atual")
        pilotos = await conexao.fetch("SELECT * FROM vw_pilotos_temporada_atual")
        return {
            "totais": totais,
            "corridas": corridas,
            "escuderias": escuderias,
            "pilotos": pilotos,
        }


async def buscar_relatorio_status() -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        return await conexao.fetch(
            "SELECT s.status, COUNT(r.id) AS total"
            " FROM results r"
            " JOIN status s ON r.status_id = s.id"
            " GROUP BY s.id, s.status"
            " ORDER BY total DESC"
        )


async def buscar_relatorio_aeroportos(nome_cidade: str) -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        return await conexao.fetch(
            "SELECT cidade_pesquisada, estado, iata_code, aeroporto, cidade_aeroporto, distancia_km, tipo"
            " FROM mv_aeroportos_cidades_br"
            " WHERE LOWER(cidade_pesquisada) = LOWER($1)"
            " ORDER BY cidade_pesquisada, estado, distancia_km",
            nome_cidade,
        )


async def buscar_relatorio_escuderias_pilotos() -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        return await conexao.fetch(
            "SELECT c.name, COUNT(DISTINCT res.driver_id) AS total_pilotos"
            " FROM constructors c"
            " LEFT JOIN results res ON res.constructor_id = c.id"
            " GROUP BY c.id, c.name"
            " ORDER BY total_pilotos DESC"
        )


async def buscar_relatorio_corridas_hierarquico() -> dict:
    pool = get_pool()
    async with pool.acquire() as conexao:
        total = await conexao.fetchval("SELECT COUNT(*) FROM races")
        por_circuito = await conexao.fetch(
            "SELECT"
            "  ci.id AS circuit_id,"
            "  ci.name AS circuito,"
            "  COUNT(DISTINCT r.id) AS total_corridas,"
            "  COUNT(DISTINCT res.race_id) AS corridas_com_resultado,"
            "  MIN(res.laps) AS min_voltas,"
            "  ROUND(AVG(res.laps)::numeric, 1) AS avg_voltas,"
            "  MAX(res.laps) AS max_voltas"
            " FROM races r"
            " JOIN circuits ci ON r.circuit_id = ci.id"
            " LEFT JOIN results res ON res.race_id = r.id"
            " GROUP BY ci.id, ci.name"
            " ORDER BY ci.name"
        )
        por_corrida = await conexao.fetch(
            "SELECT"
            "  r.circuit_id,"
            "  r.race_name,"
            "  EXTRACT(YEAR FROM r.race_date)::int AS ano,"
            "  MAX(res.laps) AS voltas,"
            "  COUNT(DISTINCT res.driver_id) AS pilotos"
            " FROM races r"
            " JOIN results res ON res.race_id = r.id"
            " GROUP BY r.circuit_id, r.id, r.race_name, r.race_date"
            " ORDER BY r.circuit_id, r.race_date"
        )
        return {
            "total": total,
            "por_circuito": por_circuito,
            "por_corrida": por_corrida,
        }


async def buscar_paises() -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        return await conexao.fetch("SELECT id, name FROM countries ORDER BY name")


async def cadastrar_escuderia(
    userid: int,
    constructor_ref: str,
    name: str,
    country_id: int,
    wikipedia_url: str | None,
) -> None:
    pool = get_pool()
    async with pool.acquire() as conexao:
        async with conexao.transaction():
            await conexao.execute(
                "INSERT INTO constructors (constructor_ref, name, country_id, wikipedia_url) VALUES ($1, $2, $3, $4)",
                constructor_ref,
                name,
                country_id,
                wikipedia_url,
            )
            await registrar_criar_escuderia(userid, conexao)


async def cadastrar_piloto(
    userid: int,
    driver_ref: str,
    given_name: str,
    family_name: str,
    date_of_birth: date,
    country_id: int,
) -> None:
    pool = get_pool()
    async with pool.acquire() as conexao:
        async with conexao.transaction():
            await conexao.execute(
                "INSERT INTO drivers (driver_ref, given_name, family_name, date_of_birth, country_id) VALUES ($1, $2, $3, $4, $5)",
                driver_ref,
                given_name,
                family_name,
                date_of_birth,
                country_id,
            )
            await registrar_criar_piloto(userid, conexao)
