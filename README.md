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
1. Create and activate a virtual environment (optional but recommended).
2. Copy `.env.example` to `.env` and set `DATABASE_URL`.
3. Install dependencies:
```bash
pip install -r requirements.txt
```
4. Run the service:
```bash
uvicorn app.main:app --reload
```

### Notes
- Endpoints are defined but return 501 Not Implemented.
- Use cases and repositories are stubs raising NotImplementedError.
- Database models and connections are scaffolded without migrations.



