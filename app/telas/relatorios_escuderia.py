from rich import box
from rich.console import Console
from rich.table import Table

from app.modulos import escuderia
from app.modulos.user import Usuario

console = Console()


async def menu_relatorios(usuario: Usuario) -> None:
    # Mesma estrutura de menu do relatorios_admin: lista as opções, lê o número
    # e chama a tela correspondente até o usuário escolher voltar
    opcoes = [
        ("Pilotos e vitórias", tela_relatorio_4),
        ("Resultados por status", tela_relatorio_5),
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


async def tela_relatorio_4(usuario: Usuario) -> None:
    # Relatório 4 pilotos da escuderia e quantas vezes cada um venceu por ela
    registros = await escuderia.buscar_relatorio_pilotos_vitorias(usuario.id_original)

    console.print()
    if not registros:
        console.print("Esta escuderia ainda não tem pilotos com resultados na base.")
        return

    tabela = Table(title="Pilotos da Escuderia e Vitórias", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Piloto", style="white")
    tabela.add_column("Vitórias", justify="right", style="yellow")
    for r in registros:
        tabela.add_row(r["piloto"], str(r["vitorias"]))
    console.print(tabela)


async def tela_relatorio_5(usuario: Usuario) -> None:
    # Relatório 5 contagem de resultados por status, só desta escuderia
    registros = await escuderia.buscar_relatorio_status_escuderia(usuario.id_original)

    console.print()
    if not registros:
        console.print("Nenhum resultado encontrado para esta escuderia.")
        return

    tabela = Table(title="Resultados por Status", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Status", style="white")
    tabela.add_column("Total", justify="right", style="cyan")
    for r in registros:
        tabela.add_row(r["status"], str(r["quantidade"]))
    console.print(tabela)