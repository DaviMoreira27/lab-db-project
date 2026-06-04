from dataclasses import dataclass
from typing import Awaitable, Callable

from app.modulos.user import Usuario

_registro: list["Tela"] = []


@dataclass
class Tela:
    nome: str
    tipos_permitidos: list[str]
    executar: Callable[[Usuario], Awaitable[None]]


def tela(nome: str, tipos_permitidos: list[str]):
    def decorador(func: Callable[[Usuario], Awaitable[None]]):
        _registro.append(Tela(nome=nome, tipos_permitidos=tipos_permitidos, executar=func))
        return func
    return decorador


def telas_disponiveis(tipo: str) -> list[Tela]:
    return [t for t in _registro if tipo in t.tipos_permitidos]
