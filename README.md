## Chat Service Skeleton (FastAPI + PostgreSQL)

This repository contains a clean architecture skeleton for a chat service with two bounded contexts: authentication and chatbot. Logic is intentionally not implemented yet; only structure, interfaces, and stubs are provided.

### Stack
- FastAPI
- PostgreSQL
- SQLAlchemy (async) + asyncpg
- Pydantic Settings

### Project Structure (Clean Architecture)
```
app/
  main.py
  api/
    v1/
      routes/
        auth.py
        chat.py
  core/
    settings.py
    db.py
  domain/
    auth/
      entities.py
      repositories.py
    chat/
      entities.py
      repositories.py
  application/
    auth/
      use_cases/
        authenticate_user.py
        register_user.py
    chat/
      use_cases/
        start_chat_session.py
        submit_user_message.py
        bot_ask_question.py
  infrastructure/
    db/
      base.py
      models/
        user.py
        chat_session.py
        message.py
      repositories/
        user_repository.py
        chat_repository.py
    auth/
      password.py
  schemas/
    auth.py
    chat.py
```

### Getting Started
1. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
source .venv/bin/activate
```
2. Copy `.env.example` to `.env` and ensure `DATABASE_URL` matches Docker Compose defaults:
```bash
cp .env.example .env
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chat_service
```
3. Start PostgreSQL using Docker:
```bash
docker compose up -d db
```
4. Install dependencies:
```bash
pip install -r requirements.txt
```
5. Initialize the database schema (creates tables):
```bash
PYTHONPATH=. python scripts/init_db.py
```
6. Run the service:
```bash
uvicorn app.main:app --reload
```
7. Open API docs:
```bash
open http://127.0.0.1:8000/docs
```

### Notes
- Endpoints are defined but return 501 Not Implemented.
- Use cases and repositories are stubs raising NotImplementedError.
- JWT helper is a stub (`app/infrastructure/auth/jwt.py`). Replace with a real implementation later.

### Troubleshooting
- ModuleNotFoundError: No module named 'app' when initializing DB:
```bash
PYTHONPATH=. python scripts/init_db.py
```
- Cannot connect to database: ensure the container is running and `DATABASE_URL` is correct:
```bash
docker compose ps
```
- Recreate tables from models (data loss):
```bash
docker compose down -v && docker compose up -d db
PYTHONPATH=. python scripts/init_db.py
```



