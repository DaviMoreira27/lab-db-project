from dataclasses import dataclass, field

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from app.modulos.admin import buscar_dados_dashboard
from app.modulos.user import Usuario

console = Console()


@dataclass
class Corrida:
    circuito: str
    data: str
    horario: str
    voltas: int


@dataclass
class EscuderiaTemporada:
    nome: str
    pontos: int


@dataclass
class PilotoTemporada:
    nome: str
    pontos: int


@dataclass
class DadosDashboardAdmin:
    total_pilotos: int = 0
    total_escuderias: int = 0
    total_temporadas: int = 0
    temporada_recente: int | None = None
    corridas: list[Corrida] = field(default_factory=list)
    escuderias: list[EscuderiaTemporada] = field(default_factory=list)
    pilotos: list[PilotoTemporada] = field(default_factory=list)

async def renderizar(usuario: Usuario) -> None:
    raw = await buscar_dados_dashboard()
    totais = raw["totais"]
    dados = DadosDashboardAdmin(
        total_pilotos=totais["pilotos"],
        total_escuderias=totais["escuderias"],
        total_temporadas=totais["temporadas"],
        temporada_recente=totais["ano_temporada_recente"],
        corridas=[
            Corrida(
                circuito=r["circuito"],
                data=r["data"].strftime("%d/%m/%Y") if r["data"] else "-",
                horario=r["horario"].strftime("%H:%M") if r["horario"] else "-",
                voltas=r["quantidade_voltas"] or 0,
            )
            for r in raw["corridas"]
        ],
        escuderias=[
            EscuderiaTemporada(nome=e["escuderia"], pontos=e["total_pontos"])
            for e in raw["escuderias"]
        ],
        pilotos=[
            PilotoTemporada(nome=p["piloto"], pontos=p["total_pontos"])
            for p in raw["pilotos"]
        ],
    )
    temporada_label = str(dados.temporada_recente) if dados.temporada_recente else "-"

    console.print()
    cabecalho = Text()
    cabecalho.append(usuario.email, style="bold white")
    cabecalho.append("  [Administrador]", style="bold yellow")
    console.print(cabecalho)
    console.rule(style="dim")

    console.print(
        f"  Pilotos: [cyan]{dados.total_pilotos}[/]    "
        f"Escuderias: [cyan]{dados.total_escuderias}[/]    "
        f"Temporadas: [cyan]{dados.total_temporadas}[/]"
    )

    console.print()
    _tabela_corridas(dados.corridas, temporada_label)

    console.print()
    _tabela_escuderias(dados.escuderias, temporada_label)

    console.print()
    _tabela_pilotos(dados.pilotos, temporada_label)

    console.print()


def _tabela_corridas(corridas: list[Corrida], temporada: str) -> None:
    tabela = Table(title=f"Corridas — Temporada {temporada}", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Circuito", style="white")
    tabela.add_column("Data", style="cyan")
    tabela.add_column("Horário", style="cyan")
    tabela.add_column("Voltas", justify="right", style="cyan")
    for c in corridas:
        tabela.add_row(c.circuito, c.data, c.horario, str(c.voltas))
    console.print(tabela)


def _tabela_escuderias(escuderias: list[EscuderiaTemporada], temporada: str) -> None:
    tabela = Table(title=f"Escuderias — Temporada {temporada}", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Escuderia", style="white")
    tabela.add_column("Pontos", justify="right", style="yellow")
    for e in escuderias:
        tabela.add_row(e.nome, str(e.pontos))
    console.print(tabela)


def _tabela_pilotos(pilotos: list[PilotoTemporada], temporada: str) -> None:
    tabela = Table(title=f"Pilotos — Temporada {temporada}", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Piloto", style="white")
    tabela.add_column("Pontos", justify="right", style="yellow")
    for p in pilotos:
        tabela.add_row(p.nome, str(p.pontos))
    console.print(tabela)
