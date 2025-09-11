from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.chat import router as chat_router
from app.core.settings import settings


def create_app() -> FastAPI:
    application = FastAPI(title="Chat Service", version="0.1.0")

    # CORS
    cors_origins = ["http://127.0.0.1:3000", "http://localhost:3000", "http://127.0.0.1:3001", "http://localhost:3001", "http://localhost:5173"]
    
    # Add production origins if in production
    if settings.app_env == "production":
        cors_origins.extend(["http://localhost", "http://127.0.0.1"])
    
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint
    @application.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "app_env": settings.app_env,
            "recommendations_enabled": settings.enable_vacancy_recommendations
        }

    # Routers
    application.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    application.include_router(chat_router, prefix="/api/v1/chat", tags=["chat"])

    return application


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

