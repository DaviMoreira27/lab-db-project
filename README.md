# lab-db-project

## Requisitos

- Python 3.13
- PostgreSQL acessível

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r require.txt
```

Copie o `.env.example` e preencha com as credenciais do banco:

```bash
cp .env.example .env
```

`.env`:
```
DB_STRING="postgresql://user:password@host:port/database"
DEV=true   # habilita logs detalhados; remova ou altere para qualquer outro valor em produção
```

## Rodar

Os comandos devem ser executados a partir da raiz do projeto (`lab-db-project/`), com o venv ativado.

Bash/Zsh:
```bash
source .venv/bin/activate
python -m app.main
```

Fish:
```fish
source .venv/bin/activate.fish
python -m app.main
```

Para login, há 3 tipos de usuário: admin, escuderias e pilotos


Admin:
```
Login: admin
Senha: admin
```

Escuderia:
```
Login: nomeEscuderia_c (exemplo: ferrari_c)
Senha: nomeEscuderia (exemplo: ferrari)
```

Piloto:
```
Login: nomePiloto_c (exemplo: hamilton_d)
Senha: nomePiloto (exemplo: hamilton)
```

---

## Estrutura do projeto

```
app/
  main.py                    — ponto de entrada, login, loop principal
  modulos/
    user.py                  — dataclass Usuario (userid, email, tipo)
    auth.py                  — autenticação (login_usuario)
    user_logging.py          — registro de ações na tabela users_log
    admin.py                 — operações de banco exclusivas do Admin
  telas/
    base.py                  — decorator @tela e registro global de telas
    navegador.py             — loop do menu, despacha dashboard por tipo
    telas.py                 — todas as telas da aplicação
    dashboard_admin.py       — dashboard do Administrador
    dashboard_escuderia.py   — dashboard da Escuderia
    dashboard_piloto.py      — dashboard do Piloto
  database/
    database_service.py      — pool asyncpg (init_pool, get_pool, close_pool)
    database_error.py        — InternalDatabaseError
```

---

## Como adicionar uma nova tela

Toda tela é uma função `async` decorada com `@tela` em `app/telas/telas.py`. O decorator recebe o nome que aparece no menu e a lista de tipos de usuário que podem vê-la.

```python
# app/telas/telas.py
from app.telas.base import tela
from app.modulos.user import Usuario

@tela("Nome no menu", tipos_permitidos=["Admin"])
async def minha_tela(usuario: Usuario) -> None:
    # lógica da tela aqui
    ...
```

Tipos disponíveis: `"Admin"`, `"Escuderia"`, `"Piloto"`. O menu é montado automaticamente — não é necessário alterar o navegador.

---

## Como adicionar acesso ao banco em uma tela

Use `get_pool()` para obter o pool e adquira uma conexão com `pool.acquire()`. Quando a operação precisar ser atômica com o registro de log, abra uma transação explícita e passe a conexão para a função de log.

```python
from app.database.database_service import get_pool
import asyncpg

pool = get_pool()
async with pool.acquire() as conexao:
    async with conexao.transaction():
        await conexao.execute("INSERT INTO ...", ...)
        await registrar_alguma_acao(usuario.userid, conexao)
```

Operações de banco mais complexas (que envolvem múltiplas queries ou são reutilizadas por mais de uma tela) devem ficar em `app/modulos/`, seguindo o padrão de `admin.py`.

---

## Como adicionar uma nova ação de log

1. Adicione o valor na constraint do banco:
```sql
ALTER TABLE users_log DROP CONSTRAINT chk_action;
ALTER TABLE users_log ADD CONSTRAINT chk_action
    CHECK (action IN ('LOGIN', 'LOGOUT', 'CRIAR_PIL', 'CRIAR_ESC', 'NOVA_ACAO'));
```

2. Adicione a função pública em `app/modulos/user_logging.py`:
```python
async def registrar_nova_acao(userid: int, conexao: Conexao = None) -> None:
    await _registrar_acao(userid, "NOVA_ACAO", conexao)
```

---

## Como atualizar a dashboard

Cada tipo de usuário tem seu próprio arquivo de dashboard isolado:

- Admin → `app/telas/dashboard_admin.py`
- Escuderia → `app/telas/dashboard_escuderia.py`
- Piloto → `app/telas/dashboard_piloto.py`

Cada arquivo expõe uma única função `async def renderizar(usuario: Usuario) -> None`. Toda a lógica de busca de dados e renderização fica dentro desse arquivo — o navegador só chama `renderizar` sem conhecer os detalhes.

Para adicionar dados reais à dashboard, substitua a chamada a `_mock()` dentro de `renderizar` por uma função que busca do banco:

```python
# antes (mock)
async def renderizar(usuario: Usuario) -> None:
    dados = _mock()
    ...

# depois (banco)
async def renderizar(usuario: Usuario) -> None:
    dados = await carregar_dados()  # função que busca do banco
    ...
```

Os dataclasses de cada dashboard (`DadosDashboardAdmin`, etc.) definem o contrato entre a camada de dados e a camada de renderização — altere-os conforme os dados necessários mudarem.
