"""Agent 长期记忆数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_memory import AgentMemory


class AgentMemoryRepository:
    """Agent 长期记忆数据访问操作。"""

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: str,
        memory_type: str,
        content: str,
        source_thread_id: str | None = None,
    ) -> AgentMemory:
        """创建一条长期记忆，不负责提交事务。"""
        memory = AgentMemory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            source_thread_id=source_thread_id,
        )

        session.add(memory)
        await session.flush()

        return memory

    @staticmethod
    async def get_by_user_id(
        session: AsyncSession,
        user_id: str,
    ) -> list[AgentMemory]:
        """查询指定用户的全部长期记忆。"""
        result = await session.scalars(
            select(AgentMemory)
            .where(AgentMemory.user_id == user_id)
            .order_by(
                AgentMemory.created_at.desc(),
                AgentMemory.id.desc(),
            )
        )

        return list(result.all())

    @staticmethod
    async def update(
        session: AsyncSession,
        memory_id: int,
        user_id: str,
        content: str,
        memory_type: str | None = None,
    ) -> AgentMemory | None:
        """更新指定用户的记忆，不负责提交事务。"""
        result = await session.scalars(
            select(AgentMemory).where(
                AgentMemory.id == memory_id,
                AgentMemory.user_id == user_id,
            )
        )
        memory = result.first()

        if memory is None:
            return None

        memory.content = content

        if memory_type is not None:
            memory.memory_type = memory_type

        await session.flush()

        return memory

    @staticmethod
    async def delete(
        session: AsyncSession,
        memory_id: int,
        user_id: str,
    ) -> bool:
        """删除指定用户的记忆，不负责提交事务。"""
        result = await session.scalars(
            select(AgentMemory).where(
                AgentMemory.id == memory_id,
                AgentMemory.user_id == user_id,
            )
        )
        memory = result.first()

        if memory is None:
            return False

        await session.delete(memory)
        await session.flush()

        return True
