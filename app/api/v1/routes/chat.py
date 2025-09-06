from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.schemas.chat import (
    StartChatSessionRequest,
    StartChatSessionResponse,
    SubmitMessageRequest,
    ChatMessageResponse,
    BotQuestionResponse,
)


router = APIRouter()


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



