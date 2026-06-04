import asyncio
import getpass
import logging

from rich.traceback import install

from app.modulos.auth import CredenciaisInvalidas, login_usuario
from app.modulos.user_logging import registrar_logout
from app.database.database_service import close_pool, init_pool
from app.telas import telas as _  # registra todas as telas
from app.telas.navegador import iniciar

logging.basicConfig(level=logging.INFO)

install(show_locals=True, max_frames=3)


async def main():
    await init_pool()

    try:
        email = input("Login: ")
        senha = getpass.getpass("Senha: ")

        try:
            usuario = await login_usuario(email, senha)
        except CredenciaisInvalidas as e:
            print(f"Erro: {e}")
            return

        await iniciar(usuario) # nao permite o registrar_logout executar ate que o usuario selecione "0 - Sair"
        await registrar_logout(usuario.userid)
    finally:
        await close_pool()


asyncio.run(main())
