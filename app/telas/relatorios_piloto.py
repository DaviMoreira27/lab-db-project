from collections import defaultdict

from rich import box
from rich.console import Console
from rich.table import Table

from app.modulos import pilotos
from app.modulos.user import Usuario

console = Console()


async def menu_relatorios(usuario: Usuario) -> None:
    opcoes = [
        ("Pontos por ano e corrida", tela_relatorio_6),
        ("Resultados por status", tela_relatorio_7),
    ]

    while True:
        console.print()
        console.rule("Relatórios", style="dim")
        for i, (nome, _) in enumerate(opcoes, 1):
            console.print(f"  {i}. {nome}")
        console.print("  0. Voltar")

        opcao = input("\nEscolha: ").strip()

        if opcao == "0":
            break
        if opcao.isdigit() and 1 <= int(opcao) <= len(opcoes):
            await opcoes[int(opcao) - 1][1](usuario)
        else:
            console.print("[red]Opção inválida[/]")


async def tela_relatorio_6(usuario: Usuario) -> None:
    driver_id = usuario.id_original if usuario.id_original else 0
    registros = await pilotos.buscar_relatorio_pontos_por_ano(driver_id)

    if not registros:
        console.print("\nNenhum ponto registrado para este pilotos.")
        return

    # agrupa corridas por ano
    por_ano: dict[int, list] = defaultdict(list)
    total_por_ano: dict[int, float] = {}
    for r in registros:
        por_ano[r["ano"]].append(r)
        total_por_ano[r["ano"]] = float(r["total_ano"])

    console.print()
    for ano in sorted(por_ano.keys()):
        corridas = por_ano[ano]
        total = total_por_ano[ano]

        tabela = Table(
            title=f"{ano}  —  Total: [yellow]{total}[/] pts",
            box=box.SIMPLE_HEAVY,
            show_lines=False,
        )
        tabela.add_column("Corrida", style="white")
        tabela.add_column("Data", style="cyan")
        tabela.add_column("Pontos", justify="right", style="yellow")

        for c in corridas:
            tabela.add_row(
                c["corrida"],
                c["data"].strftime("%d/%m/%Y") if c["data"] else "-",
                str(float(c["pontos"])),
            )
        console.print(tabela)


async def tela_relatorio_7(usuario: Usuario) -> None:
    driver_id = usuario.id_original if usuario.id_original else 0
    registros = await pilotos.buscar_relatorio_status(driver_id)

    if not registros:
        console.print("\nNenhum resultado encontrado para este piloto.")
        return

    console.print()
    tabela = Table(
        title="Resultados por Status",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
    )
    tabela.add_column("Status", style="white")
    tabela.add_column("Total", justify="right", style="cyan")

    for r in registros:
        tabela.add_row(r["status"], str(r["quantidade"]))
    console.print(tabela)
