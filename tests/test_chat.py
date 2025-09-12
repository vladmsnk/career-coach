import os
import sys
import asyncio
from datetime import datetime
from uuid import uuid4
from typing import Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.v1.routes.chat import chat_websocket, get_chat_repository
from app.domain.chat.entities import ChatSession, Message
from app.domain.chat.repositories import ChatRepository
from app.domain.chat.questions import QUESTIONS
from app.infrastructure.auth.jwt import create_access_token
from app.main import app


class InMemoryChatRepository(ChatRepository):
    def __init__(self) -> None:
        self.sessions: dict[str, list[ChatSession]] = {}
        self.messages: dict[str, list[Message]] = {}

    async def create_session(
        self,
        user_id,
        *,
        status: str = "active",
        question_index: int = 0,
        answers_count: int = 0,
    ):
        session = ChatSession(
            id=uuid4(),
            user_id=user_id,
            created_at=datetime.utcnow(),
            status=status,
            question_index=question_index,
            answers_count=answers_count,
            current_module="current_profile",
            collected_data={},
        )
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

    async def get_session(self, session_id):
        for sessions in self.sessions.values():
            for s in sessions:
                if s.id == session_id:
                    return s
        return None

    async def update_session(
        self,
        session_id,
        *,
        status: Optional[str] = None,
        question_index: Optional[int] = None,
        answers_count: Optional[int] = None,
    ):
        for sessions in self.sessions.values():
            for s in sessions:
                if s.id == session_id:
                    if status is not None:
                        s.status = status
                    if question_index is not None:
                        s.question_index = question_index
                    if answers_count is not None:
                        s.answers_count = answers_count
                    return s
        raise KeyError("session not found")

    async def update_session_data(
        self,
        session_id,
        question_id: str,
        answer: str,
    ) -> None:
        """Update collected_data with new question-answer pair"""
        for sessions in self.sessions.values():
            for s in sessions:
                if s.id == session_id:
                    s.collected_data[question_id] = answer
                    return
        raise KeyError("session not found")


class FakeWebSocket:
    def __init__(self, inputs: list[str], disconnect_on_empty: bool = False, delay: float = 0.0) -> None:
        self.inputs = inputs
        self.disconnect_on_empty = disconnect_on_empty
        self.delay = delay
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.sent.append(data)

    async def receive_text(self):
        if not self.inputs:
            if self.disconnect_on_empty:
                from fastapi import WebSocketDisconnect

                raise WebSocketDisconnect()
            await asyncio.sleep(3600)
        await asyncio.sleep(self.delay)
        return self.inputs.pop(0)

    async def close(self, code: int = 1000):
        self.closed = True


def test_chat_flow():
    repo = InMemoryChatRepository()
    app.dependency_overrides[get_chat_repository] = lambda: repo
    user_id = str(uuid4())
    token = create_access_token(user_id)
    # Test all 12 questions - need to provide correct answers for each question type
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
    ws = FakeWebSocket(answers, disconnect_on_empty=True, delay=0.02)
    asyncio.run(chat_websocket(ws, token, repo))
    prompts = [m["id"] for m in ws.sent if "id" in m]
    # Check that we have all 12 questions
    expected_ids = [q["id"] for q in QUESTIONS]
    assert prompts == expected_ids
    assert ws.sent[-1]["event"] == "finished"
    app.dependency_overrides.clear()


def test_resume_session_returns_previous_messages():
    repo = InMemoryChatRepository()
    app.dependency_overrides[get_chat_repository] = lambda: repo
    user_id = str(uuid4())
    token = create_access_token(user_id)
    ws1 = FakeWebSocket(["Бэкенд-разработчик"], disconnect_on_empty=True)
    asyncio.run(chat_websocket(ws1, token, repo))
    # Provide remaining answers to complete the interview (questions 2-12)
    remaining_answers = [
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
    ws2 = FakeWebSocket(remaining_answers, disconnect_on_empty=True, delay=0.02)
    asyncio.run(chat_websocket(ws2, token, repo))
    assert ws2.sent[0] == {"role": "bot", "content": QUESTIONS[0]["prompt"]}
    assert ws2.sent[1] == {"role": "user", "content": "Бэкенд-разработчик"}
    prompts = [m["id"] for m in ws2.sent if "id" in m]
    # Should have remaining 11 questions (all except the first one)
    expected_ids = [q["id"] for q in QUESTIONS[1:]]
    assert prompts == expected_ids
    assert ws2.sent[-1]["event"] == "finished"
    app.dependency_overrides.clear()


def test_each_user_has_own_session():
    repo = InMemoryChatRepository()
    app.dependency_overrides[get_chat_repository] = lambda: repo
    user1 = create_access_token(str(uuid4()))
    user2 = create_access_token(str(uuid4()))
    ws1 = FakeWebSocket(["Бэкенд-разработчик"], disconnect_on_empty=True)
    asyncio.run(chat_websocket(ws1, user1, repo))
    ws2 = FakeWebSocket(["Фронтенд-разработчик"], disconnect_on_empty=True)
    asyncio.run(chat_websocket(ws2, user2, repo))
    # Each user should start with the first question
    assert ws2.sent[0]["id"] == QUESTIONS[0]["id"]
    app.dependency_overrides.clear()
