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
