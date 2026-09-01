# AI Knowledge Assistant

A small FastAPI service that will provide the foundation for the AI Knowledge Assistant project.

## Current requirements

- Python 3.11
- FastAPI 0.141.1
- pypdf 6.8.0
- psycopg 3.3.5
- python-dotenv 1.2.3
- python-multipart 0.0.22
- qdrant-client 1.19.0
- sentence-transformers 5.2.2
- SQLAlchemy 2.0.52
- Uvicorn 0.52.4

## Setup

1. Copy the example environment configuration.

   ```powershell
   Copy-Item .env.example .env
   ```

   The `.env` file is for local settings and is ignored by Git. Do not commit it.

2. Create and activate a Python 3.11 virtual environment.

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the project dependencies.

   ```powershell
   python -m pip install -e .
   ```

## Run the server

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

The server is available at `http://127.0.0.1:8000`.

## Local infrastructure

Start PostgreSQL and Qdrant with Docker Compose:

```powershell
docker compose up -d
```

Check the running services:

```powershell
docker compose ps
```

Stop and remove the Compose containers:

```powershell
docker compose down
```

Do not use `docker compose down -v` if you want to keep the PostgreSQL and
Qdrant data stored in Docker volumes.

## Health endpoint

`GET /health` returns:

```json
{"status": "ok"}
```
