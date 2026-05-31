import asyncio
import logging

from rich.traceback import install

from app.database.database_service import close_pool, init_pool

logging.basicConfig(level=logging.INFO)

install(show_locals=True, max_frames=3)

async def main():
    print("Start")
    await init_pool()
    print("Conexão com o banco estabelecida")
    await close_pool()


asyncio.run(main())
