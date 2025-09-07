from uuid import UUID

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
from app.infrastructure.auth.jwt import decode_access_token
from app.infrastructure.db.repositories.chat_repository import SqlAlchemyChatRepository


router = APIRouter()


def get_chat_repository(session: AsyncSession = Depends(get_db_session)) -> ChatRepository:
    return SqlAlchemyChatRepository(session)


async def safe_send_json(websocket: WebSocket, data: dict) -> bool:
    """Safely send JSON data through WebSocket, return False if connection is closed"""
    try:
        await websocket.send_json(data)
        return True
    except WebSocketDisconnect:
        return False
    except Exception:
        return False


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
        await websocket.accept()
        user_id = decode_access_token(token)
        if not user_id:
            await websocket.close(code=1008)
            return
        user_uuid = UUID(user_id)
        session = await repo.get_latest_session(user_uuid)
        if not session or session.answers_count >= len(QUESTIONS) or session.status == "finished":
            session = await repo.create_session(user_uuid, question_index=1)
        user_messages = await repo.list_messages(session.id)

        for i in range(1, session.question_index + 1):
            question = QUESTIONS[i - 1]
            if i <= session.answers_count and i <= len(user_messages):
                if not await safe_send_json(websocket, {"role": "bot", "content": question["prompt"]}):
                    return
                if not await safe_send_json(websocket, {"role": "user", "content": user_messages[i - 1].content}):
                    return
            elif i == session.question_index:
                if not await safe_send_json(websocket, {"id": question["id"], "prompt": question["prompt"]}):
                    return

        last_user_message = (
            user_messages[-1].content if user_messages and session.answers_count > 0 else None
        )

        if session.question_index > session.answers_count:
            question = QUESTIONS[session.question_index - 1]
            while True:
                try:
                    user_reply = await websocket.receive_text()
                except WebSocketDisconnect:
                    return
                if last_user_message is not None and user_reply == last_user_message:
                    if not await safe_send_json(websocket, {"error": "duplicate"}):
                        return
                    if not await safe_send_json(websocket, {"id": question["id"], "prompt": question["prompt"]}):
                        return
                    continue
                await repo.add_message(session.id, "user", user_reply)
                last_user_message = user_reply
                session = await repo.update_session(
                    session.id, answers_count=session.answers_count + 1
                )
                break

        idx = session.answers_count
        while idx < len(QUESTIONS):
            question = QUESTIONS[idx]
            while True:
                if not await safe_send_json(websocket, {"id": question["id"], "prompt": question["prompt"]}):
                    return
                await repo.update_session(session.id, question_index=idx + 1)
                try:
                    user_reply = await websocket.receive_text()
                except WebSocketDisconnect:
                    return
                if last_user_message is not None and user_reply == last_user_message:
                    if not await safe_send_json(websocket, {"error": "duplicate"}):
                        return
                    continue
                await repo.add_message(session.id, "user", user_reply)
                last_user_message = user_reply
                await repo.update_session(session.id, answers_count=idx + 1)
                break
            idx += 1
        await repo.update_session(session.id, status="finished")
        if not await safe_send_json(websocket, {"event": "finished"}):
            return
        await websocket.close()
        
    except WebSocketDisconnect:
        # Клиент отключился - это нормально, не логируем как ошибку
        pass
    except Exception as e:
        # Логируем только неожиданные ошибки
        print(f"Unexpected error in WebSocket: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass

