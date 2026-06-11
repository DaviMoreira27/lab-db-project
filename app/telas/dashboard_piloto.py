from dataclasses import dataclass, field

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from app.modulos.pilotos import buscar_dados_dashboard
from app.modulos.user import Usuario

console = Console()


@dataclass
class StatCircuito:
    ano: int
    circuito: str
    pontos: float
    vitorias: int
    corridas: int


@dataclass
class DadosDashboardPiloto:
    nome: str
    primeiro_ano: int | None = None
    ultimo_ano: int | None = None
    stats: list[StatCircuito] = field(default_factory=list)


async def renderizar(usuario: Usuario) -> None:
    # id_original do usuário logado é o driver_id
    driver_id = usuario.id_original

    raw = await buscar_dados_dashboard(driver_id)

    anos = raw["anos"]
    dados = DadosDashboardPiloto(
        nome=usuario.email,
        primeiro_ano=anos["primeiro_ano"] if anos else None,
        ultimo_ano=anos["ultimo_ano"] if anos else None,
        stats=[
            StatCircuito(
                ano=s["ano"],
                circuito=s["circuito"],
                pontos=float(s["pontos"]),
                vitorias=s["vitorias"],
                corridas=s["corridas"],
            )
            for s in raw["stats"]
        ],
    )

    console.print()
    cabecalho = Text()
    cabecalho.append(dados.nome, style="bold white")
    cabecalho.append("  [Piloto]", style="bold cyan")
    console.print(cabecalho)
    console.rule(style="dim")

    primeiro = str(dados.primeiro_ano) if dados.primeiro_ano else "-"
    ultimo = str(dados.ultimo_ano) if dados.ultimo_ano else "-"
    console.print(f"  Ativo na F1: [cyan]{primeiro}[/] → [cyan]{ultimo}[/]")

    console.print()
    _tabela_stats(dados.stats)
    console.print()


def _tabela_stats(stats: list[StatCircuito]) -> None:
    tabela = Table(
        title="Desempenho por Ano e Circuito",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    tabela.add_column("Ano", style="cyan", justify="right")
    tabela.add_column("Circuito", style="white")
    tabela.add_column("Pontos", style="yellow", justify="right")
    tabela.add_column("Vitórias", style="green", justify="right")
    tabela.add_column("Corridas", style="white", justify="right")

    for s in stats:
        tabela.add_row(
            str(s.ano),
            s.circuito,
            str(s.pontos),
            str(s.vitorias),
            str(s.corridas),
        )
    console.print(tabela)