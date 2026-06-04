import asyncpg

from app.database.database_service import get_pool


async def _registrar_acao(userid: int, acao: str, conexao: asyncpg.Connection | None = None) -> None:
    if conexao is not None:
        await conexao.execute(
            "INSERT INTO users_log (userid, action) VALUES ($1, $2)",
            userid,
            acao,
        )
    else:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO users_log (userid, action) VALUES ($1, $2)",
                userid,
                acao,
            )


async def registrar_login(userid: int, conexao: asyncpg.Connection) -> None:
    await _registrar_acao(userid, "LOGIN", conexao)


async def registrar_logout(userid: int) -> None:
    await _registrar_acao(userid, "LOGOUT")
