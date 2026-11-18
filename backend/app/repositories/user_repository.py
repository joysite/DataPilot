"""用户数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.ingestion import UserImport


class UserRepository:
    """用户数据访问操作。"""

    @staticmethod
    async def get_existing_ids(
        session: AsyncSession,
        user_ids: list[str],
    ) -> set[str]:
        """查询已经存在的用户 ID。"""
        if not user_ids:
            return set()

        result = await session.scalars(
            select(User.user_id).where(User.user_id.in_(user_ids))
        )
        return set(result.all())

    @staticmethod
    async def bulk_insert(
        session: AsyncSession,
        users: list[UserImport],
    ) -> int:
        """批量插入用户记录，不负责提交事务。"""
        if not users:
            return 0

        existing_ids = await UserRepository.get_existing_ids(
            session,
            [user.user_id for user in users],
        )

        new_users = [
            User(
                user_id=user.user_id,
                register_time=user.register_time,
                region=user.region,
            )
            for user in users
            if user.user_id not in existing_ids
        ]

        if not new_users:
            return 0

        session.add_all(new_users)
        await session.flush()

        return len(new_users)
