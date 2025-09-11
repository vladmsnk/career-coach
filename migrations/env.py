import asyncio
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from app.core.settings import settings
from app.infrastructure.db.base import Base

config = context.config
# Keep URL from alembic.ini or test override if provided; do not override here

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    # Получаем конфигурацию из alembic.ini
    configuration = config.get_section(config.config_ini_section, {})
    
    # Проверяем DATABASE_URL из переменных окружения (приоритет)
    database_url = os.getenv('DATABASE_URL')
    
    # Если DATABASE_URL есть, используем его вместо alembic.ini
    if database_url and database_url.strip():
        print(f"🔧 Using DATABASE_URL from environment: {database_url}")
        configuration["sqlalchemy.url"] = database_url
    else:
        original_url = configuration.get("sqlalchemy.url", "")
        print(f"📄 Using alembic.ini URL: {original_url}")
    
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def main() -> None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())


main()