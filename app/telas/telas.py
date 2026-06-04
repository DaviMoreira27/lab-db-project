from app.modulos.user import Usuario
from app.telas.base import tela


@tela("Meu perfil", tipos_permitidos=["Admin", "Escuderia", "Piloto"])
async def meu_perfil(usuario: Usuario) -> None:
    print(f"\nLogin: {usuario.email}")
    print(f"Tipo:  {usuario.tipo}")


@tela("Painel administrativo", tipos_permitidos=["Admin"])
async def painel_admin(usuario: Usuario) -> None:
    print("\nPainel administrativo")


@tela("Relatório de escuderias", tipos_permitidos=["Admin", "Escuderia"])
async def relatorio_escuderias(usuario: Usuario) -> None:
    print("\nRelatório de escuderias")


@tela("Relatório de pilotos", tipos_permitidos=["Admin", "Piloto"])
async def relatorio_pilotos(usuario: Usuario) -> None:
    print("\nRelatório de pilotos")
