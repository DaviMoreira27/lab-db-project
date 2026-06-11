from app.modulos.user import Usuario
from app.modulos.user_logging import registrar_login
from app.database.database_service import get_pool


class CredenciaisInvalidas(Exception):
    pass


async def login_usuario(email: str, senha: str) -> Usuario:
    pool = get_pool()
    async with pool.acquire() as conexao:
        async with conexao.transaction():
            registro = await conexao.fetchrow(
                # a lib de bycrpt do pyhton e a do postgres esperam formatos de hashes levemente diferentes
                # entao pelos usuarios ja terem sido criados via pgcrypt, e necessario usa-lo tbm para o login
                "SELECT userid, login, tipo, id_original FROM users WHERE login = $1 AND password = crypt($2, password)",
                email,
                senha,
            )

            if registro is None:
                raise CredenciaisInvalidas("Email ou senha inválidos")

            usuario = Usuario(
                userid=registro["userid"],
                email=registro["login"],
                tipo=registro["tipo"],
                id_original=registro["id_original"],
            )
            await registrar_login(usuario.userid, conexao)

    return usuario