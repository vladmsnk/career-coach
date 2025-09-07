from dataclasses import dataclass
from uuid import UUID

from app.domain.chat.repositories import ChatRepository
from app.domain.chat.questions import QUESTIONS


@dataclass
class BotAskQuestionUseCase:
    chat_repository: ChatRepository

    async def execute(self, session_id: UUID) -> str:
        session = await self.chat_repository.get_session(session_id)
        if not session:
            raise ValueError("session not found")
        if session.question_index >= len(QUESTIONS):
            await self.chat_repository.update_session(session_id, status="finished")
            raise StopAsyncIteration
        question = QUESTIONS[session.question_index]["prompt"]
        await self.chat_repository.update_session(
            session_id, question_index=session.question_index + 1
        )
        return question



