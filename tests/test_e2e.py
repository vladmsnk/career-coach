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

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="error")


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
        async_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
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

                uri = f"ws://127.0.0.1:8000/api/v1/chat/ws?token={token}"
                async with websockets.connect(uri) as ws:
                    for answer in ["IT", "Developer", "5"]:
                        data = json.loads(await ws.recv())
                        assert "id" in data
                        await ws.send(answer)
                    final = json.loads(await ws.recv())
                    assert final["event"] == "finished"

            asyncio.run(_chat())
        finally:
            server.terminate()
            server.join()
