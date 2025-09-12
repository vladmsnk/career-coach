import os
import sys
import time
import json
import asyncio
import uuid
from multiprocessing import Process

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
from alembic import command
from alembic.config import Config
from testcontainers.postgres import PostgresContainer


def _run_server() -> None:
    import sys
    import importlib
    import uvicorn
    
    # Force reload questions module to avoid caching issues in subprocess
    try:
        # First import the module if not loaded
        import app.domain.chat.questions
        # Then force reload it to get latest changes
        importlib.reload(app.domain.chat.questions)
    except ImportError:
        pass  # Module might not be available in subprocess

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")


def _wait_for_server(url: str, timeout: float = 15) -> None:
    for _ in range(int(timeout / 0.5)):
        try:
            requests.get(url)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Server did not start in time")


def test_successful_dialog() -> None:
    """E2E test for complete chat dialog with new IT-focused questions"""
    with PostgresContainer("postgres:15") as postgres:
        db_url = postgres.get_connection_url()
        # Normalize to async driver regardless of original driver
        async_url = (
            db_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
            .replace("postgresql://", "postgresql+asyncpg://")
        )
        os.environ["DATABASE_URL"] = async_url
        os.environ["PYTHONPATH"] = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # Set other required environment variables for testing
        os.environ.setdefault("SECRET_KEY", "test_secret_key")
        os.environ.setdefault("ENABLE_VACANCY_RECOMMENDATIONS", "false")  # Disable recommendations for faster test
        os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
        os.environ.setdefault("QDRANT_COLLECTION", "vacancies_tasks")

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", async_url)
        command.upgrade(alembic_cfg, "head")

        server = Process(target=_run_server, daemon=True)
        server.start()
        try:
            _wait_for_server("http://127.0.0.1:8000/docs")

            # Generate unique user data for each test run
            test_id = str(uuid.uuid4())[:8]
            payload = {"login": f"user_{test_id}", "email": f"user_{test_id}@example.com", "password": "secret"}
            r = requests.post("http://127.0.0.1:8000/api/v1/auth/register", json=payload)
            assert r.status_code == 201

            r = requests.post(
                "http://127.0.0.1:8000/api/v1/auth/login",
                json={"login": f"user_{test_id}", "password": "secret"},
            )
            assert r.status_code == 200
            token = r.json()["access_token"]

            async def _chat() -> None:
                import websockets
                import logging

                logger = logging.getLogger("test_e2e")
                logger.setLevel(logging.INFO)

                uri = f"ws://127.0.0.1:8000/api/v1/chat/ws?token={token}"
                async with websockets.connect(uri) as ws:
                    # Answer all 12 questions for complete interview (correctly matched to question types)
                    answers = [
                        "Бэкенд-разработчик",                    # 1. professional_area (select)
                        "Python-разработчик",                    # 2. current_position (text)
                        "5",                                     # 3. years_experience (number)
                        "Разработал микросервисы на Python",     # 4. work_experience_projects (text)
                        "Фулстек-разработчик",                   # 5. target_area (select)
                        "Разработка ПО",                         # 6. preferred_activities (text)
                        "Senior",                                # 7. position_level_ambitions (select) 
                        "150000",                                # 8. salary_expectations (range)
                        "Python, FastAPI, PostgreSQL",          # 9. current_skills (text)
                        "Docker, Kubernetes, Git",               # 10. tools_experience (text)
                        "Коммуникация, лидерство",               # 11. soft_skills (text)
                        "МГУ, курсы по Python"                   # 12. education (text)
                        ]
                    
                    for i, answer in enumerate(answers):
                        raw = await ws.recv()
                        data = json.loads(raw)
                        logger.info("received question %d: %s", i+1, data)
                        assert "id" in data, f"unexpected message: {data}"
                        logger.info("send answer %d: %s", i+1, answer)
                        await ws.send(answer)
                    
                    # Теперь с включенными рекомендациями сначала приходят карьерная консультация, потом рекомендации, потом finished
                    first_msg = json.loads(await ws.recv())
                    logger.info("first_msg: %s", first_msg)
                    
                    if first_msg["event"] == "career_consultation":
                        # Проверяем что карьерная консультация содержит данные
                        assert "data" in first_msg
                        assert "consultation" in first_msg["data"]
                        assert len(first_msg["data"]["consultation"]) > 0
                        logger.info("✅ Получена карьерная консультация (длина: %d символов)", len(first_msg["data"]["consultation"]))

                        # Получаем рекомендации
                        recommendations_msg = json.loads(await ws.recv())
                        logger.info("recommendations_msg: %s", recommendations_msg)
                        assert recommendations_msg["event"] == "recommendations"
                        assert "data" in recommendations_msg
                        assert "hh_ids" in recommendations_msg["data"]
                        assert len(recommendations_msg["data"]["hh_ids"]) == 5
                        logger.info("✅ Получены рекомендации с HH IDs: %s", recommendations_msg["data"]["hh_ids"])

                        # Получаем финальное сообщение
                        final = json.loads(await ws.recv())
                        logger.info("final: %s", final)
                        assert final["event"] == "finished"
                    elif first_msg["event"] == "recommendations":
                        # Если карьерная консультация отключена, но рекомендации включены
                        assert "data" in first_msg
                        assert "hh_ids" in first_msg["data"]
                        assert len(first_msg["data"]["hh_ids"]) == 5
                        logger.info("✅ Получены рекомендации с HH IDs: %s", first_msg["data"]["hh_ids"])

                        # Получаем финальное сообщение
                        final = json.loads(await ws.recv())
                        logger.info("final: %s", final)
                        assert final["event"] == "finished"
                    else:
                        # Если рекомендации отключены, должно сразу прийти finished
                        assert first_msg["event"] == "finished"

            asyncio.run(_chat())
        finally:
            server.terminate()
            server.join()
