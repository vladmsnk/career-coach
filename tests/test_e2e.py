import os
import time
import json
import asyncio
import uuid
from multiprocessing import Process

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
                    # Answer all 12 questions for complete interview
                    answers = [
                        "Бэкенд-разработчик", "5", "Разработал микросервисы на Python",
                        "Full-stack Developer", "Разработка ПО", "Senior Developer", 
                        "150000", "Программирование", "Python", "Коммуникация", 
                        "МГУ, курсы по Python", "Изучение Kubernetes"
                    ]
                    
                    for i, answer in enumerate(answers):
                        raw = await ws.recv()
                        data = json.loads(raw)
                        logger.info("received question %d: %s", i+1, data)
                        assert "id" in data, f"unexpected message: {data}"
                        logger.info("send answer %d: %s", i+1, answer)
                        await ws.send(answer)
                    
                    final = json.loads(await ws.recv())
                    logger.info("final: %s", final)
                    assert final["event"] == "finished"

            asyncio.run(_chat())
        finally:
            server.terminate()
            server.join()
