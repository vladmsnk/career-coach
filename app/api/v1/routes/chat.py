from uuid import UUID

import asyncio
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.post("/sessions", response_model=StartChatSessionResponse, status_code=201)
async def start_chat_session(payload: StartChatSessionRequest) -> StartChatSessionResponse:
    raise HTTPException(status_code=501, detail="Not implemented")


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
)
async def submit_user_message(session_id: UUID, payload: SubmitMessageRequest) -> ChatMessageResponse:
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/sessions/{session_id}/next", response_model=BotQuestionResponse)
async def get_next_bot_question(session_id: UUID) -> BotQuestionResponse:
    raise HTTPException(status_code=501, detail="Not implemented")


@router.websocket("/ws")
async def chat_websocket(
    websocket: WebSocket,
    token: str,
    repo: ChatRepository = Depends(get_chat_repository),
):
    await websocket.accept()
    user_id = decode_access_token(token)
    if not user_id:
        await websocket.close(code=1008)
        return
    user_uuid = UUID(user_id)
    session = await repo.get_latest_session(user_uuid)
    messages = []
    if session:
        messages = await repo.list_messages(session.id)
        answers_count = len([m for m in messages if m.role == "user"])
        if answers_count >= len(QUESTIONS):
            session = await repo.create_session(user_uuid)
            messages = []
            answers_count = 0
    else:
        session = await repo.create_session(user_uuid)
        answers_count = 0

    for m in messages:
        await websocket.send_json({"role": m.role, "content": m.content})

    last_user_message = next((m.content for m in reversed(messages) if m.role == "user"), None)
    idx = answers_count
    while idx < len(QUESTIONS):
        question = QUESTIONS[idx]
        await repo.add_message(session.id, "bot", question["prompt"])
        while True:
            await websocket.send_json({"id": question["id"], "prompt": question["prompt"]})
            try:
                user_reply = await websocket.receive_text()
            except WebSocketDisconnect:
                return
            if last_user_message is not None and user_reply == last_user_message:
                await websocket.send_json({"error": "duplicate"})
                continue
            await repo.add_message(session.id, "user", user_reply)
            last_user_message = user_reply
            while True:
                try:
                    await asyncio.wait_for(websocket.receive_text(), timeout=0.01)
                except asyncio.TimeoutError:
                    break
                except WebSocketDisconnect:
                    return
            break
        idx += 1
    await websocket.send_json({"event": "finished"})
    await websocket.close()



