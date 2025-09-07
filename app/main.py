from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.chat import router as chat_router


def create_app() -> FastAPI:
    application = FastAPI(title="Chat Service", version="0.1.0")

    # CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    application.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    application.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

