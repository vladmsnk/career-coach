from fastapi import FastAPI

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.chat import router as chat_router


def create_app() -> FastAPI:
    application = FastAPI(title="Chat Service", version="0.1.0")

    # Routers
    application.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    application.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

    return application


app = create_app()



