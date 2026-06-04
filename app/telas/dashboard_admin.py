from dataclasses import dataclass, field

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

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


def _mock() -> DadosDashboardAdmin:
    return DadosDashboardAdmin(
        total_pilotos=857,
        total_escuderias=210,
        total_temporadas=74,
        temporada_recente=2024,
        corridas=[
            Corrida("Autódromo José Carlos Pace", "02/03/2024", "15:00", 71),
            Corrida("Circuit de Monaco", "26/05/2024", "15:00", 78),
            Corrida("Silverstone Circuit", "07/07/2024", "15:00", 52),
            Corrida("Monza Circuit", "01/09/2024", "15:00", 53),
            Corrida("Yas Marina Circuit", "08/12/2024", "17:00", 58),
        ],
        escuderias=[
            EscuderiaTemporada("McLaren", 593),
            EscuderiaTemporada("Ferrari", 557),
            EscuderiaTemporada("Red Bull", 410),
            EscuderiaTemporada("Mercedes", 409),
            EscuderiaTemporada("Aston Martin", 86),
        ],
        pilotos=[
            PilotoTemporada("Max Verstappen", 331),
            PilotoTemporada("Lando Norris", 279),
            PilotoTemporada("Charles Leclerc", 245),
            PilotoTemporada("Oscar Piastri", 233),
            PilotoTemporada("Carlos Sainz", 290),
        ],
    )


async def renderizar(usuario: Usuario) -> None:
    dados = _mock()
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
