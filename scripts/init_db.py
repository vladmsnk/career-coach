import asyncio

from app.infrastructure.db.base import Base
from app.infrastructure.db.models import user, chat_session, message  # noqa: F401
from app.core.settings import settings
from sqlalchemy.ext.asyncio import create_async_engine


async def main() -> None:
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())


