from rich.console import Console
from rich.text import Text

from app.modulos.user import Usuario

console = Console()


async def renderizar(usuario: Usuario) -> None:
    console.print()
    cabecalho = Text()
    cabecalho.append(usuario.email, style="bold white")
    cabecalho.append("  [Escuderia]", style="bold yellow")
    console.print(cabecalho)
    console.rule(style="dim")
    console.print()
