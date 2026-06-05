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
