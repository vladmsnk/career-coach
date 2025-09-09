from uuid import UUID
from typing import Optional, Tuple

import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.chat.use_cases.start_chat_session import StartChatSessionUseCase
from app.application.chat.use_cases.submit_user_message import SubmitUserMessageUseCase
from app.application.chat.use_cases.bot_ask_question import BotAskQuestionUseCase
from app.schemas.chat import (
    StartChatSessionRequest,
    StartChatSessionResponse,
    SubmitMessageRequest,
    ChatMessageResponse,
    BotQuestionResponse,
)
from app.core.db import get_db_session
from app.domain.chat.questions import QUESTIONS
from app.domain.chat.repositories import ChatRepository
from app.domain.chat.entities import ChatSession
from app.infrastructure.auth.jwt import decode_access_token
from app.infrastructure.db.repositories.chat_repository import SqlAlchemyChatRepository


router = APIRouter()


def get_chat_repository(session: AsyncSession = Depends(get_db_session)) -> ChatRepository:
    return SqlAlchemyChatRepository(session)


class WebSocketHandler:
    """Handles WebSocket communication for chat sessions"""
    
    def __init__(self, websocket: WebSocket, repo: ChatRepository):
        self.websocket = websocket
        self.repo = repo
        
    async def send_json(self, data: dict) -> bool:
        """Safely send JSON data through WebSocket"""
        try:
            await self.websocket.send_json(data)
            return True
        except (WebSocketDisconnect, Exception):
            return False
    
    async def receive_text(self) -> str:
        """Receive text with proper disconnect handling"""
        return await self.websocket.receive_text()
    
    async def send_previous_messages(self, session: ChatSession, user_messages: list) -> bool:
        """Send chat history to restore session (only completed Q&A pairs)"""
        for i in range(session.answers_count):
            if i < len(user_messages):
                question = QUESTIONS[i]
                # Send previous Q&A pair
                if not await self.send_json({"role": "bot", "content": question["prompt"]}):
                    return False
                if not await self.send_json({"role": "user", "content": user_messages[i].content}):
                    return False
        return True
    
    def validate_answer(self, answer: str, question_data: dict) -> Optional[str]:
        """Validate answer based on question type"""
        q_type = question_data.get("type", "string")
        
        if q_type == "select":
            options = question_data.get("options", [])
            if answer not in options:
                return f"Выберите один из вариантов: {', '.join(options)}"
        
        elif q_type == "multiselect":
            # Simple comma-separated validation for now
            options = question_data.get("options", [])
            selected = [s.strip() for s in answer.split(",") if s.strip()]
            if not selected:
                return "Выберите хотя бы один вариант"
            invalid = [s for s in selected if s not in options]
            if invalid:
                return f"Недопустимые варианты: {', '.join(invalid)}"
        
        elif q_type == "number":
            try:
                num = int(answer)
                min_val = question_data.get("min", 0)
                max_val = question_data.get("max", 100)
                if not (min_val <= num <= max_val):
                    return f"Число должно быть от {min_val} до {max_val}"
            except ValueError:
                return "Введите корректное число"
        
        elif q_type == "range":
            try:
                num = int(answer)
                min_val = question_data.get("min", 0)
                max_val = question_data.get("max", 100)
                if not (min_val <= num <= max_val):
                    return f"Значение должно быть от {min_val} до {max_val}"
            except ValueError:
                return "Введите корректное число"
        
        elif q_type in ["string", "text"]:
            max_len = question_data.get("max_length", 1000)
            if len(answer) > max_len:
                return f"Максимальная длина: {max_len} символов"
            if len(answer.strip()) == 0:
                return "Ответ не может быть пустым"
        
        return None

    def normalize_answer(self, answer: Optional[str], question_type: str) -> Optional[str]:
        """Normalize answer for comparison"""
        if answer is None:
            return None
        
        if question_type == "multiselect":
            # Normalize multiselect as sorted set
            items = sorted([s.strip().lower() for s in answer.split(",") if s.strip()])
            return ",".join(items)
        
        return answer.strip().lower()

    async def handle_question_cycle(self, question_data: dict, session_id: UUID, last_user_message: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        """Handle a single question-answer cycle with enhanced protocol"""
        while True:
            # Расширенный формат вопроса (обратно-совместимый)
            question_payload = {
                "id": question_data["id"],
                "prompt": question_data["prompt"],
                # Новые поля (опциональные)
                "type": question_data.get("type", "string"),
                "module": question_data.get("module", "context"),
                "module_title": question_data.get("module_title", ""),
                "progress": {
                    "current": question_data.get("global_index", 0) + 1,
                    "total": question_data.get("total_questions", 15)
                }
            }
            
            # Добавляем constraints для типизированных вопросов
            if question_data.get("type") == "select":
                question_payload["options"] = question_data.get("options", [])
            elif question_data.get("type") == "multiselect":
                question_payload["options"] = question_data.get("options", [])
                question_payload["multiple"] = True
            elif question_data.get("type") == "number":
                question_payload["constraints"] = {
                    "min": question_data.get("min", 0),
                    "max": question_data.get("max", 100)
                }
            elif question_data.get("type") == "range":
                question_payload["constraints"] = {
                    "min": question_data.get("min", 0),
                    "max": question_data.get("max", 100),
                    "step": question_data.get("step", 1)
                }
            elif question_data.get("type") in ["string", "text"]:
                question_payload["constraints"] = {
                    "max_length": question_data.get("max_length", 1000)
                }
            
            # Send enhanced question
            if not await self.send_json(question_payload):
                return None, None
                
            # Receive answer
            try:
                user_reply = await self.receive_text()
            except WebSocketDisconnect:
                return None, None
            
            # Basic validation of answer
            validation_error = self.validate_answer(user_reply, question_data)
            if validation_error:
                if not await self.send_json({
                    "error": {
                        "code": "validation_failed",
                        "message": validation_error,
                        "details": {}
                    }
                }):
                    return None, None
                continue
            
            # Check for duplicate answer (normalized comparison)
            normalized_reply = self.normalize_answer(user_reply, question_data.get("type", "string"))
            normalized_last = self.normalize_answer(last_user_message, question_data.get("type", "string")) if last_user_message else None
            
            if normalized_last and normalized_reply == normalized_last:
                if not await self.send_json({"error": "duplicate"}):
                    return None, None
                continue
            
            # Save message and return
            await self.repo.add_message(session_id, "user", user_reply)
            return user_reply, user_reply
    
    async def complete_session(self, session_id: UUID) -> bool:
        """Mark session as finished and send completion message"""
        await self.repo.update_session(session_id, status="finished")
        if await self.send_json({"event": "finished"}):
            await self.websocket.close()
            return True
        return False


def authenticate_user(token: str) -> Optional[UUID]:
    """Authenticate user and return UUID"""
    user_id = decode_access_token(token)
    return UUID(user_id) if user_id else None


async def get_or_create_session(user_uuid: UUID, repo: ChatRepository) -> ChatSession:
    """Get existing active session or create new one"""
    session = await repo.get_latest_session(user_uuid)
    if not session or session.answers_count >= len(QUESTIONS) or session.status == "finished":
        session = await repo.create_session(user_uuid, question_index=1)
    return session


@router.post("/sessions", response_model=StartChatSessionResponse, status_code=201)
async def start_chat_session(
    payload: StartChatSessionRequest,
    repo: ChatRepository = Depends(get_chat_repository),
) -> StartChatSessionResponse:
    session_id, question, created_at = await StartChatSessionUseCase(repo).execute(
        payload.user_id
    )
    return StartChatSessionResponse(
        session_id=session_id, created_at=created_at, question=question
    )


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
)
async def submit_user_message(
    session_id: UUID,
    payload: SubmitMessageRequest,
    repo: ChatRepository = Depends(get_chat_repository),
) -> ChatMessageResponse:
    message = await SubmitUserMessageUseCase(repo).execute(session_id, payload.content)
    return ChatMessageResponse(
        message_id=message.id,
        session_id=message.session_id,
        content=message.content,
        role=message.role,
        created_at=message.created_at,
    )


@router.get("/sessions/{session_id}/next", response_model=BotQuestionResponse)
async def get_next_bot_question(
    session_id: UUID, repo: ChatRepository = Depends(get_chat_repository)
) -> BotQuestionResponse:
    try:
        question = await BotAskQuestionUseCase(repo).execute(session_id)
    except StopAsyncIteration:
        raise HTTPException(status_code=404, detail="No more questions")
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
    return BotQuestionResponse(session_id=session_id, question=question)


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    token: str,
    repo: ChatRepository = Depends(get_chat_repository),
):
    try:
        # 1. Initialize connection
        await websocket.accept()
        user_uuid = authenticate_user(token)
        if not user_uuid:
            await websocket.close(code=1008)
            return
        
        handler = WebSocketHandler(websocket, repo)
        
        # 2. Get or create session
        session = await get_or_create_session(user_uuid, repo)
        
        # 3. Send chat history (only completed Q&A pairs)
        user_messages = await repo.list_messages(session.id)
        if not await handler.send_previous_messages(session, user_messages):
            return
        
        # 4. Handle all remaining questions (starting from answers_count)
        last_user_message = user_messages[-1].content if user_messages and session.answers_count > 0 else None
        
        for idx in range(session.answers_count, len(QUESTIONS)):
            question = QUESTIONS[idx]
            # Add total_questions for progress calculation
            question_with_meta = {**question, "total_questions": len(QUESTIONS)}
            
            await repo.update_session(session.id, question_index=idx + 1)
            
            user_reply, last_user_message = await handler.handle_question_cycle(question_with_meta, session.id, last_user_message)
            if user_reply is None:  # Connection closed
                return
            
            # Save answer to collected_data
            await repo.update_session_data(session.id, question["id"], user_reply)
            await repo.update_session(session.id, answers_count=idx + 1)
        
        # 5. Complete session
        await handler.complete_session(session.id)
        
    except WebSocketDisconnect:
        # Normal disconnect - no logging needed
        pass
    except Exception as e:
        print(f"Unexpected WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass
