# KlipAI Backend

## Setup with uv

```bash
uv sync
```

## Run Django commands

```bash
uv run python manage.py migrate
uv run python manage.py runserver
```

## Add or update dependencies

```bash
uv add <package>
uv lock --upgrade
```
