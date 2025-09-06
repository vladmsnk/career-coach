import os
import os
import sys
import asyncio
from datetime import datetime
from uuid import uuid4

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.v1.routes.chat import chat_websocket, get_chat_repository
from app.domain.chat.entities import ChatSession, Message
from app.domain.chat.repositories import ChatRepository
from app.infrastructure.auth.jwt import create_access_token
from app.main import app


class InMemoryChatRepository(ChatRepository):
    def __init__(self) -> None:
        self.sessions: dict[str, list[ChatSession]] = {}
        self.messages: dict[str, list[Message]] = {}

    async def create_session(self, user_id):
        session = ChatSession(id=uuid4(), user_id=user_id, created_at=datetime.utcnow())
        self.sessions.setdefault(str(user_id), []).append(session)
        self.messages[str(session.id)] = []
        return session

    async def add_message(self, session_id, role: str, content: str):
        msg = Message(id=uuid4(), session_id=session_id, role=role, content=content, created_at=datetime.utcnow())
        self.messages[str(session_id)].append(msg)
        return msg

    async def list_messages(self, session_id):
        return self.messages.get(str(session_id), [])

    async def get_latest_session(self, user_id):
        sessions = self.sessions.get(str(user_id))
        if sessions:
            return sessions[-1]
        return None


class FakeWebSocket:
    def __init__(self, inputs: list[str]) -> None:
        self.inputs = inputs
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.sent.append(data)

    async def receive_text(self):
        return self.inputs.pop(0)

    async def close(self, code: int = 1000):
        self.closed = True


def test_chat_flow():
    repo = InMemoryChatRepository()
    app.dependency_overrides[get_chat_repository] = lambda: repo
    user_id = str(uuid4())
    token = create_access_token(user_id)
    ws = FakeWebSocket(["IT", "Developer", "5"])
    asyncio.run(chat_websocket(ws, token, repo))
    prompts = [m["id"] for m in ws.sent[:-1]]
    assert prompts == ["domain", "position", "years"]
    assert ws.sent[-1]["event"] == "finished"
    app.dependency_overrides.clear()
