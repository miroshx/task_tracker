import asyncio
import pytest
from tracker_app.database import Base, engine
from tracker_app.config import settings


@pytest.fixture
async def prepare_database():
    assert settings.MODE == 'TEST'
    print("Создание таблиц...________________________________________________")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы успешно созданы.")

def test_hehe():
    assert 1 == 1

