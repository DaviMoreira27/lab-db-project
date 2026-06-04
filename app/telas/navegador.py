from app.modulos.user import Usuario
from app.telas import dashboard_admin, dashboard_escuderia, dashboard_piloto
from app.telas.base import telas_disponiveis

_dashboards = {
    "Admin": dashboard_admin.renderizar,
    "Escuderia": dashboard_escuderia.renderizar,
    "Piloto": dashboard_piloto.renderizar,
}


async def iniciar(usuario: Usuario) -> None:
    await _dashboards[usuario.tipo](usuario)

    while True:
        disponiveis = telas_disponiveis(usuario.tipo)

        for i, t in enumerate(disponiveis, 1):
            print(f"{i}. {t.nome}")
        print("0. Sair")

        opcao = input("\nEscolha: ").strip()

        if opcao == "0":
            break
        if opcao.isdigit() and 1 <= int(opcao) <= len(disponiveis):
            await disponiveis[int(opcao) - 1].executar(usuario)
        else:
            print("Opção inválida")
