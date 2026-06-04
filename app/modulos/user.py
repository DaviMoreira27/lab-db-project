from dataclasses import dataclass


@dataclass
class Usuario:
    userid: int
    email: str
    tipo: str
