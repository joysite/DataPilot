"""数据库初始化。"""

from sqlalchemy import text

import app.models  # noqa: F401
from app.database.base import Base
from app.database.connection import engine


async def init_db() -> None:
    """创建所有 ORM 模型对应的数据表。"""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    """检查数据库连接是否正常。"""
    async with engine.connect() as connection:
        result = await connection.execute(text("SELECT 1"))
        return result.scalar_one() == 1
