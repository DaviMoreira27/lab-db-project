import time
import logging

import asyncpg

from app.database.database_service import get_pool

logger = logging.getLogger(__name__)


def _log_query(label: str, elapsed_s: float) -> None:
    logger.debug("[query] %s — %.1f ms", label, elapsed_s * 1000)


async def buscar_dados_dashboard(driver_id: int) -> dict:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        anos = await conexao.fetchrow(
            "SELECT * FROM get_driver_years($1)",
            driver_id,
        )
        _log_query("(func)get_driver_years", time.perf_counter() - t)

        t = time.perf_counter()
        stats = await conexao.fetch(
            "SELECT * FROM get_driver_stats($1)",
            driver_id,
        )
        _log_query("(func)get_driver_stats", time.perf_counter() - t)

        return {"anos": anos, "stats": stats}


async def buscar_relatorio_pontos_por_ano(driver_id: int) -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        result = await conexao.fetch(
            "SELECT * FROM get_driver_points_by_year($1)",
            driver_id,
        )
        _log_query("(func)get_driver_points_by_year", time.perf_counter() - t)
        return result


async def buscar_relatorio_status(driver_id: int) -> list[asyncpg.Record]:
    pool = get_pool()
    async with pool.acquire() as conexao:
        t = time.perf_counter()
        result = await conexao.fetch(
            "SELECT * FROM get_driver_status_count($1)",
            driver_id,
        )
        _log_query("(func)get_driver_status_count", time.perf_counter() - t)
        return result