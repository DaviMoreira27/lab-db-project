import logging
from datetime import date, datetime

import asyncpg

from app.modulos import admin
from app.modulos.user import Usuario
from app.telas.base import tela
from app.telas.relatorios_admin import menu_relatorios
from app.telas.relatorios_piloto import menu_relatorios as menu_relatorios_piloto

logger = logging.getLogger(__name__)


@tela("Meu perfil", tipos_permitidos=["Escuderia", "Piloto"])
async def meu_perfil(usuario: Usuario) -> None:
    print(f"\nLogin: {usuario.email}")
    print(f"Tipo:  {usuario.tipo}")


@tela("Relatório de escuderias", tipos_permitidos=["Escuderia"])
async def relatorio_escuderias(usuario: Usuario) -> None:
    print("\nRelatório de escuderias")


@tela("Relatório de pilotos", tipos_permitidos=["Piloto"])
async def relatorio_pilotos(usuario: Usuario) -> None:
    await menu_relatorios_piloto(usuario)


@tela("Relatórios", tipos_permitidos=["Admin"])
async def relatorios_admin(usuario: Usuario) -> None:
    await menu_relatorios(usuario)


def _selecionar_pais(paises: list) -> int:
    for i, p in enumerate(paises, 1):
        print(f"{i}. {p['name']}")
    while True:
        opcao = input("Escolha o país (número): ").strip()
        if opcao.isdigit() and 1 <= int(opcao) <= len(paises):
            return paises[int(opcao) - 1]["id"]
        print("Opção inválida")


@tela("Cadastrar Escuderia", tipos_permitidos=["Admin"])
async def tela_cadastrar_escuderia(usuario: Usuario) -> None:
    constructor_ref = input("\nRef da escuderia: ").strip()
    if not constructor_ref:
        print("Campo obrigatório.")
        return

    name = input("Nome: ").strip()
    if not name:
        print("Campo obrigatório.")
        return

    paises = await admin.buscar_paises()
    country_id = _selecionar_pais(paises)

    wikipedia_url = input("Wikipedia URL (opcional): ").strip() or None

    try:
        await admin.cadastrar_escuderia(usuario.userid, constructor_ref, name, country_id, wikipedia_url)
        print(f"Escuderia '{name}' cadastrada com sucesso.")
    except asyncpg.UniqueViolationError as e:
        logger.error("Erro ao cadastrar escuderia: %s", e)
        print("Erro: ref ou nome já em uso.")
    except asyncpg.PostgresError as e:
        logger.error("Erro ao cadastrar escuderia: %s", e)
        print("Erro ao cadastrar escuderia.")


@tela("Cadastrar Piloto", tipos_permitidos=["Admin"])
async def tela_cadastrar_piloto(usuario: Usuario) -> None:
    driver_ref = input("\nRef do piloto: ").strip()
    if not driver_ref:
        print("Campo obrigatório.")
        return

    given_name = input("Nome: ").strip()
    if not given_name:
        print("Campo obrigatório.")
        return

    family_name = input("Sobrenome: ").strip()
    if not family_name:
        print("Campo obrigatório.")
        return

    date_of_birth: date
    while True:
        raw = input("Data de nascimento (YYYY-MM-DD): ").strip()
        try:
            date_of_birth = datetime.strptime(raw, "%Y-%m-%d").date()
            break
        except ValueError:
            print("Formato inválido. Use YYYY-MM-DD.")

    paises = await admin.buscar_paises()
    country_id = _selecionar_pais(paises)

    try:
        await admin.cadastrar_piloto(usuario.userid, driver_ref, given_name, family_name, date_of_birth, country_id)
        print(f"Piloto '{given_name} {family_name}' cadastrado com sucesso.")
    except asyncpg.UniqueViolationError as e:
        logger.error("Erro ao cadastrar piloto: %s", e)
        print("Erro: driver_ref já em uso.")
    except asyncpg.PostgresError as e:
        logger.error("Erro ao cadastrar piloto: %s", e)
        print("Erro ao cadastrar piloto.")
