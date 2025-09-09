import os
import time
import json
import asyncio
from multiprocessing import Process

import requests
from alembic import command
from alembic.config import Config
from testcontainers.postgres import PostgresContainer


def _run_server() -> None:
    import uvicorn

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

            payload = {"login": "user", "email": "user@example.com", "password": "secret"}
            r = requests.post("http://127.0.0.1:8000/api/v1/auth/register", json=payload)
            assert r.status_code == 201

            r = requests.post(
                "http://127.0.0.1:8000/api/v1/auth/login",
                json={"login": "user", "password": "secret"},
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
                    # Answer all 15 questions for complete interview
                    answers = [
                        "IT", "Developer", "5", "3", "Проект 1", 
                        "IT", "Backend", "Техническая работа", "Senior", "100000", 
                        "Программирование", "Microsoft Excel", "Коммуникация", "ВУЗ", "React"
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
