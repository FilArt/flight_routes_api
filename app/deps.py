from databases import Database
from sqlalchemy.ext.asyncio import create_async_engine

from .models import metadata
from .settings import Settings


async def create_db_and_tables():
    settings = get_settings()

    engine = create_async_engine(settings.db_url)
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)


def get_settings():
    return Settings()


async def get_db():
    settings = get_settings()
    async with Database(settings.db_url) as db:
        yield db
