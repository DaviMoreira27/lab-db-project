from app.modulos.user import Usuario
from app.telas.base import telas_disponiveis
from app.telas.dashboard import _mock, renderizar


async def iniciar(usuario: Usuario) -> None:
    renderizar(usuario, _mock())

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
