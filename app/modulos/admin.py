import asyncpg
import logging
import time
from datetime import date

from app.database.database_service import get_pool
from app.modulos.user_logging import registrar_criar_escuderia, registrar_criar_piloto

logger = logging.getLogger(__name__)


def _log_query(label: str, elapsed_s: float) -> None:
    logger.debug("[query] %s — %.1f ms", label, elapsed_s * 1000)


async def buscar_dados_dashboard() -> dict:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        # Contagens globais via PKs, sem índices adicionais.
        totais = await conexao.fetchrow(
            "SELECT"
            " (SELECT COUNT(*) FROM drivers) AS pilotos,"
            " (SELECT COUNT(*) FROM constructors) AS escuderias,"
            " (SELECT COUNT(*) FROM seasons) AS temporadas,"
            " (SELECT MAX(year) FROM seasons) AS ano_temporada_recente"
        )
        _log_query("(query) dashboard_totais", time.perf_counter() - t)

        t = time.perf_counter()
        # View definida em dashboard_admin.sql. Usa idx_races_season_id e idx_results_race_id.
        corridas = await conexao.fetch("SELECT * FROM vw_corridas_temporada_atual")
        _log_query("(view)vw_corridas_temporada_atual", time.perf_counter() - t)

        t = time.perf_counter()
        # View definida em dashboard_admin.sql. Usa idx_standings_season_round e idx_constructor_standings_standing_id.
        escuderias = await conexao.fetch("SELECT * FROM vw_escuderias_temporada_atual")
        _log_query("(view)vw_escuderias_temporada_atual", time.perf_counter() - t)

        t = time.perf_counter()
        # View definida em dashboard_admin.sql. Usa idx_standings_season_round e idx_driver_standings_standing_id.
        pilotos = await conexao.fetch("SELECT * FROM vw_pilotos_temporada_atual")
        _log_query("(view)vw_pilotos_temporada_atual", time.perf_counter() - t)

        return {
            "totais": totais,
            "corridas": corridas,
            "escuderias": escuderias,
            "pilotos": pilotos,
        }


async def buscar_relatorio_status() -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        # JOIN com agregação: agrupa todos os resultados por status e conta ocorrências.
        # O JOIN results -> status usa a PK de status(id); sem índice adicional necessário
        # pois status é uma tabela pequena (sequential scan é mais rápido que index scan).
        result = await conexao.fetch(
            "SELECT s.status, COUNT(r.id) AS total"
            " FROM results r"
            " JOIN status s ON r.status_id = s.id"
            " GROUP BY s.id, s.status"
            " ORDER BY total DESC"
        )
        _log_query("(query)relatorio_status", time.perf_counter() - t)
        return result


async def buscar_relatorio_aeroportos(nome_cidade: str) -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        # Consulta a view materializada mv_aeroportos_cidades_br, que pré-computou
        # as distâncias haversine. O filtro LOWER usa idx_mv_aeroportos_cidade
        # (índice funcional criado em relatorios_admin.sql), evitando sequential scan.
        result = await conexao.fetch(
            "SELECT cidade_pesquisada, estado, iata_code, aeroporto, cidade_aeroporto, distancia_km, tipo"
            " FROM mv_aeroportos_cidades_br"
            " WHERE LOWER(cidade_pesquisada) = LOWER($1)"
            " ORDER BY cidade_pesquisada, estado, distancia_km",
            nome_cidade,
        )
        _log_query("(view_materialized)relatorio_aeroportos", time.perf_counter() - t)
        return result


async def buscar_relatorio_escuderias_pilotos() -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        # LEFT JOIN para incluir escuderias sem resultados (COUNT retorna 0).
        # O JOIN results -> constructors usa idx_results_constructor_id
        # (criado em relatorios_admin.sql), evitando sequential scan em results.
        result = await conexao.fetch(
            "SELECT c.name, COUNT(DISTINCT res.driver_id) AS total_pilotos"
            " FROM constructors c"
            " LEFT JOIN results res ON res.constructor_id = c.id"
            " GROUP BY c.id, c.name"
            " ORDER BY total_pilotos DESC"
        )
        _log_query("(query)relatorio_escuderias_pilotos", time.perf_counter() - t)
        return result


async def buscar_relatorio_corridas_hierarquico() -> dict:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        # Contagem total de corridas, usada como nível 1 do relatório hierárquico.
        total = await conexao.fetchval("SELECT COUNT(*) FROM races")
        _log_query("(query)relatorio_corridas_total", time.perf_counter() - t)

        t = time.perf_counter()
        # Nível 2: agrega por circuito com estatísticas de voltas (MIN, AVG, MAX).
        # LEFT JOIN para incluir corridas sem resultados registrados.
        # O JOIN results -> races usa idx_results_race_id.
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
        _log_query("(query)relatorio_corridas por_circuito", time.perf_counter() - t)

        t = time.perf_counter()
        # Nível 3: detalha cada corrida com voltas e número de pilotos participantes.
        # JOIN results -> races usa idx_results_race_id.
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
        _log_query("(query)relatorio_corridas por_corrida", time.perf_counter() - t)

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
        # A transação garante que a trigger trg_sync_constructor (que insere em
        # USERS) e o registro em USERS_LOG sejam confirmados juntos ou
        # revertidos em caso de erro, incluindo conflito de login já existente.
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
        # Mesma lógica de transação do cadastrar_escuderia: a trigger
        # trg_sync_driver cria o usuário em USERS dentro desta transação.
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
