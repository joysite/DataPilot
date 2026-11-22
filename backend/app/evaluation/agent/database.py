"""Agent 评测专用数据库管理。"""

from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.models  # noqa: F401
from app.core.config import settings
from app.database.base import Base


def _resolve_database_path(database_url: str) -> Path:
    """解析 SQLite 数据库文件的绝对路径。"""

    url = make_url(database_url)

    if url.drivername != "sqlite+aiosqlite":
        raise ValueError("评测数据库必须使用 sqlite+aiosqlite")

    if not url.database or url.database == ":memory:":
        raise ValueError("评测数据库必须使用独立的 SQLite 文件")

    return Path(url.database).expanduser().resolve()


def create_evaluation_database(
    database_url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """创建隔离的评测数据库及 Session 工厂。"""

    evaluation_path = _resolve_database_path(database_url)
    production_path = _resolve_database_path(settings.database_url)

    if evaluation_path == production_path:
        raise ValueError("评测数据库不能与正式业务数据库使用同一个文件")

    engine = create_async_engine(
        database_url,
        echo=False,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        """为评测数据库连接启用外键约束。"""

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine, session_factory


async def initialize_evaluation_database(engine: AsyncEngine) -> None:
    """创建评测数据库所需的 ORM 表结构。"""

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_evaluation_database(engine: AsyncEngine) -> None:
    """释放评测数据库连接池。"""

    await engine.dispose()
