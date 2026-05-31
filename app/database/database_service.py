import logging
import os

import asyncpg
import dotenv

from app.database.database_error import InternalDatabaseError

logger = logging.getLogger(__name__)
dotenv.load_dotenv()

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    try:
        _pool = await asyncpg.create_pool(os.environ["DB_STRING"])
    except Exception as e:
        logger.error(f"Erro ao criar pool de conexões: {e}")
        raise InternalDatabaseError("Falha ao inicializar pool de conexões") from e


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise InternalDatabaseError("Pool não inicializado")
    return _pool
