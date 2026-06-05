from collections import defaultdict

from rich import box
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

from app.modulos import admin
from app.modulos.user import Usuario

console = Console()

# GeoNames admin1_code (coluna GN) → ISO-3166-2 para estados brasileiros.
# Fonte: https://www.geonames.org/countries/BR/brazil.html
_ADMIN1_BR: dict[str, str] = {
    "01": "AC",
    "02": "AL",
    "04": "AM",
    "03": "AP",
    "05": "BA",
    "06": "CE",
    "07": "DF",
    "08": "ES",
    "29": "GO",
    "13": "MA",
    "15": "MG",
    "11": "MS",
    "14": "MT",
    "16": "PA",
    "17": "PB",
    "30": "PE",
    "20": "PI",
    "18": "PR",
    "21": "RJ",
    "22": "RN",
    "24": "RO",
    "25": "RR",
    "23": "RS",
    "26": "SC",
    "28": "SE",
    "27": "SP",
    "31": "TO",
}


async def menu_relatorios(usuario: Usuario) -> None:
    opcoes = [
        ("Resultados por status", tela_relatorio_1),
        ("Aeroportos próximos a cidade", tela_relatorio_2),
        ("Escuderias, pilotos e corridas", tela_relatorio_3),
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


async def tela_relatorio_1(usuario: Usuario) -> None:
    registros = await admin.buscar_relatorio_status()

    console.print()
    tabela = Table(title="Resultados por Status", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Status", style="white")
    tabela.add_column("Total", justify="right", style="cyan")
    for r in registros:
        tabela.add_row(r["status"], str(r["total"]))
    console.print(tabela)


async def tela_relatorio_2(usuario: Usuario) -> None:
    nome = input("\nNome da cidade: ").strip()
    if not nome:
        console.print("[red]Nome obrigatório.[/]")
        return

    registros = await admin.buscar_relatorio_aeroportos(nome)

    if not registros:
        console.print(f"\nNenhum aeroporto encontrado para cidades brasileiras com nome '{nome}'.")
        return

    console.print()
    por_cidade: dict[tuple, list] = defaultdict(list)
    for r in registros:
        por_cidade[(r["cidade_pesquisada"], r["estado"] or "")].append(r)

    for (cidade, admin1_code), aeroportos in por_cidade.items():
        uf = _ADMIN1_BR.get(admin1_code, admin1_code)
        label = f"{cidade} ({uf})" if uf else cidade
        tabela = Table(
            title=f"Aeroportos próximos a {label} (≤ 100 km)",
            box=box.SIMPLE_HEAVY,
            show_lines=False,
        )
        tabela.add_column("IATA", style="cyan")
        tabela.add_column("Aeroporto", style="white")
        tabela.add_column("Cidade", style="white")
        tabela.add_column("Distância (km)", justify="right", style="yellow")
        tabela.add_column("Tipo", style="dim")
        for a in aeroportos:
            tabela.add_row(
                a["iata_code"] or "-",
                a["aeroporto"],
                a["cidade_aeroporto"],
                str(a["distancia_km"]),
                a["tipo"],
            )
        console.print(tabela)


async def tela_relatorio_3(usuario: Usuario) -> None:
    escuderias = await admin.buscar_relatorio_escuderias_pilotos()
    hierarquico = await admin.buscar_relatorio_corridas_hierarquico()

    console.print()
    tabela = Table(title="Escuderias e Pilotos", box=box.SIMPLE_HEAVY, show_lines=False)
    tabela.add_column("Escuderia", style="white")
    tabela.add_column("Pilotos", justify="right", style="cyan")
    for e in escuderias:
        tabela.add_row(e["name"], str(e["total_pilotos"]))
    console.print(tabela)

    console.print()
    corridas_por_circuito: dict[int, list] = defaultdict(list)
    for c in hierarquico["por_corrida"]:
        corridas_por_circuito[c["circuit_id"]].append(c)

    arvore = Tree(f"Corridas — total: [cyan]{hierarquico['total']}[/]")
    for circuito in hierarquico["por_circuito"]:
        cid = circuito["circuit_id"]

        min_voltas = circuito['min_voltas'] if circuito['min_voltas'] is not None else '-'
        avg_voltas = circuito['avg_voltas'] if circuito['avg_voltas'] is not None else '-'
        max_voltas = circuito['max_voltas'] if circuito['max_voltas'] is not None else '-'

        ramo_circuito = arvore.add(
            f"[white]{circuito['circuito']}[/]  "
            f"[dim]{circuito['total_corridas']} corridas ({circuito['corridas_com_resultado']} com resultados)  "
            f"voltas min/avg/max: {min_voltas}/{avg_voltas}/{max_voltas}[/]"
        )
        for corrida in corridas_por_circuito.get(cid, []):
            ramo_circuito.add(
                f"[dim]{corrida['race_name']} ({corrida['ano']})[/]  "
                f"[cyan]{corrida['voltas']} voltas[/]  "
                f"[yellow]{corrida['pilotos']} pilotos[/]"
            )
    console.print(arvore)
