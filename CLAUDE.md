# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a clean architecture career coaching chat service with FastAPI backend and React frontend. The service conducts structured interviews through a chatbot to provide personalized career advice for IT professionals.

## Common Development Commands

### Backend (Python/FastAPI)
```bash
# Setup virtual environment and dependencies
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Database setup
docker compose up -d db
PYTHONPATH=. python scripts/init_db.py

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest
pytest tests/test_auth.py  # Single test file
pytest tests/test_chat.py -v  # Verbose output

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Frontend (React/Vite)
```bash
# From ui/ directory
npm install
npm run dev      # Development server on localhost:3000
npm run build    # Production build
npm run preview  # Preview production build
```

## Architecture

### Clean Architecture Structure
- **Domain**: Core business entities and repository interfaces (`app/domain/`)
  - `auth/` - User authentication domain
  - `chat/` - Chat session and messaging domain
- **Application**: Use cases and business logic (`app/application/`)
- **Infrastructure**: External concerns like databases and auth (`app/infrastructure/`)
- **API**: HTTP endpoints and request/response schemas (`app/api/v1/`)

### Key Components

#### Interview System
- Structured interview modules defined in `app/domain/chat/questions.py`
- Three modules: context, goals, skills
- Questions support multiple types: text, select, multiselect, number, range
- Session state tracks current module, question index, and collected answers

#### Database Models
- SQLAlchemy async models in `app/infrastructure/db/models/`
- Repository pattern for data access
- Alembic for database migrations

#### Frontend Structure
- React with Vite build system
- Components in `ui/src/`
- CORS configured for localhost:3000

## Testing Approach

Tests use pytest with in-memory repositories for unit testing. Test files include:
- `test_auth.py` - Authentication flow testing
- `test_chat.py` - Chat session management
- `test_questions.py` - Interview question logic
- `test_e2e.py` - End-to-end scenarios

Use `asyncio.run()` for testing async functions and `pytest.raises()` for exception testing.

## Development Notes

- Database URL configured via `.env` file (copy from `.env.example`)
- API documentation available at `/docs` when server is running
- CORS allows React dev server at localhost:3000
- Use `PYTHONPATH=.` prefix for running scripts from project root
- Repository interfaces defined in domain layer, implementations in infrastructure

## Environment Setup

Required environment variables in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/chat_service
SECRET_KEY=changeme
APP_ENV=dev
```