from dataclasses import dataclass

from rich.console import Console
from rich.text import Text

from app.modulos.escuderia import buscar_dados_dashboard_escuderia
from app.modulos.user import Usuario

console = Console()


@dataclass
class DadosDashboardEscuderia:
    escuderia: str
    qtd_pilotos: int
    qtd_vitorias: int
    primeiro_ano: int | None
    ultimo_ano: int | None


async def renderizar(usuario: Usuario) -> None:
    # O id_original do usuário escuderia é o constructor_id. A função do banco
    # devolve nome, pilotos, vitórias e o intervalo de anos numa linha só.
    raw = await buscar_dados_dashboard_escuderia(usuario.id_original)

    console.print()
    if raw is None:
        console.print("[red]Não foi possível carregar os dados da escuderia.[/]")
        console.print()
        return

    dados = DadosDashboardEscuderia(
        escuderia=raw["escuderia"],
        qtd_pilotos=raw["qtd_pilotos"] or 0,
        qtd_vitorias=raw["qtd_vitorias"] or 0,
        primeiro_ano=raw["primeiro_ano"],
        ultimo_ano=raw["ultimo_ano"],
    )

    cabecalho = Text()
    cabecalho.append(dados.escuderia, style="bold white")
    cabecalho.append("  [Escuderia]", style="bold yellow")
    console.print(cabecalho)
    console.rule(style="dim")

    if dados.primeiro_ano and dados.ultimo_ano:
        periodo = f"{dados.primeiro_ano} a {dados.ultimo_ano}"
    else:
        periodo = "sem dados"

    console.print(
        f"  Pilotos associados: [cyan]{dados.qtd_pilotos}[/]    "
        f"Vitórias: [yellow]{dados.qtd_vitorias}[/]    "
        f"Período na base: [cyan]{periodo}[/]"
    )
    console.print()