"""Agent 长期记忆业务服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_memory import AgentMemory
from app.repositories.agent_memory_repository import AgentMemoryRepository


class AgentMemoryService:
    """Agent 长期记忆管理服务。"""

    MEMORY_TYPES = {
        "preference",
        "business_context",
        "instruction",
    }

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        """校验用户 ID。"""
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("用户 ID 不能为空")

        return user_id.strip()

    @classmethod
    def _validate_memory_type(cls, memory_type: str) -> str:
        """校验记忆类型。"""
        if memory_type not in cls.MEMORY_TYPES:
            raise ValueError(f"不支持的记忆类型：{memory_type}")

        return memory_type

    @staticmethod
    def _validate_content(content: str) -> str:
        """校验记忆内容。"""
        if not isinstance(content, str) or not content.strip():
            raise ValueError("记忆内容不能为空")

        return content.strip()

    @staticmethod
    def _validate_thread_id(
        source_thread_id: str | None,
    ) -> str | None:
        """校验来源会话 ID。"""
        if source_thread_id is None:
            return None

        if not isinstance(source_thread_id, str) or not source_thread_id.strip():
            raise ValueError("来源会话 ID 不能为空字符串")

        return source_thread_id.strip()

    async def create_memory(
        self,
        session: AsyncSession,
        user_id: str,
        memory_type: str,
        content: str,
        source_thread_id: str | None = None,
    ) -> AgentMemory:
        """创建一条长期记忆。"""
        user_id = self._validate_user_id(user_id)
        memory_type = self._validate_memory_type(memory_type)
        content = self._validate_content(content)
        source_thread_id = self._validate_thread_id(source_thread_id)

        return await AgentMemoryRepository.create(
            session=session,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            source_thread_id=source_thread_id,
        )

    async def get_user_memories(
        self,
        session: AsyncSession,
        user_id: str,
    ) -> list[AgentMemory]:
        """获取指定用户的全部长期记忆。"""
        user_id = self._validate_user_id(user_id)

        return await AgentMemoryRepository.get_by_user_id(
            session=session,
            user_id=user_id,
        )

    async def update_memory(
        self,
        session: AsyncSession,
        memory_id: int,
        user_id: str,
        content: str,
        memory_type: str | None = None,
    ) -> AgentMemory | None:
        """更新指定用户的长期记忆。"""
        if (
            isinstance(memory_id, bool)
            or not isinstance(memory_id, int)
            or memory_id <= 0
        ):
            raise ValueError("记忆 ID 必须是正整数")

        user_id = self._validate_user_id(user_id)
        content = self._validate_content(content)

        if memory_type is not None:
            memory_type = self._validate_memory_type(memory_type)

        return await AgentMemoryRepository.update(
            session=session,
            memory_id=memory_id,
            user_id=user_id,
            content=content,
            memory_type=memory_type,
        )

    async def delete_memory(
        self,
        session: AsyncSession,
        memory_id: int,
        user_id: str,
    ) -> bool:
        """删除指定用户的长期记忆。"""
        if (
            isinstance(memory_id, bool)
            or not isinstance(memory_id, int)
            or memory_id <= 0
        ):
            raise ValueError("记忆 ID 必须是正整数")

        user_id = self._validate_user_id(user_id)

        return await AgentMemoryRepository.delete(
            session=session,
            memory_id=memory_id,
            user_id=user_id,
        )
