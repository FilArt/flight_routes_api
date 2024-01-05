import httpx
import pytest
from databases import Database
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from app.deps import get_db
from app.models import metadata
from app.settings import Settings
from main import app

TEST_DB_NAME = "test"


async def get_db_override():
    settings = Settings(DB_NAME=TEST_DB_NAME)
    async with Database(settings.db_url) as db:
        yield db


@pytest.fixture(autouse=True, scope="session")
async def clear_db():
    settings = Settings(DB_NAME="postgres")
    async with Database(settings.db_url) as db:
        await db.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME};")
        await db.execute(f"CREATE DATABASE {TEST_DB_NAME};")

    settings = Settings(DB_NAME=TEST_DB_NAME)
    engine: AsyncEngine = create_async_engine(settings.db_url)
    async with engine.begin() as conn:
        conn: AsyncConnection
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS Postgis;"))
        await conn.run_sync(metadata.create_all)


@pytest.fixture
async def db():
    settings = Settings(DB_NAME=TEST_DB_NAME)
    async with Database(settings.db_url) as db:
        yield db


@pytest.fixture(name="client")
async def client_fixture():
    app.dependency_overrides[get_db] = get_db_override

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()
