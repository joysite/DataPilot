"""受限业务明细查询数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.product import Product
from app.models.user import User


class QueryRepository:
    """提供白名单范围内的业务明细查询。"""

    @staticmethod
    async def query_orders(
        session: AsyncSession,
        limit: int = 20,
        order_status: str | None = None,
        user_id: str | None = None,
        product_id: str | None = None,
    ) -> list[dict]:
        """按条件查询订单明细。"""
        statement = select(
            Order.order_id,
            Order.user_id,
            Order.product_id,
            Order.order_amount,
            Order.order_status,
            Order.order_time,
        )

        if order_status is not None:
            statement = statement.where(Order.order_status == order_status)

        if user_id is not None:
            statement = statement.where(Order.user_id == user_id)

        if product_id is not None:
            statement = statement.where(Order.product_id == product_id)

        statement = statement.order_by(
            Order.order_time.desc(),
            Order.order_id.desc(),
        ).limit(limit)

        result = await session.execute(statement)

        return [dict(row) for row in result.mappings().all()]

    @staticmethod
    async def query_products(
        session: AsyncSession,
        limit: int = 20,
    ) -> list[dict]:
        """查询商品明细。"""
        statement = (
            select(
                Product.product_id,
                Product.product_name,
                Product.category,
                Product.price,
            )
            .order_by(Product.product_id.asc())
            .limit(limit)
        )

        result = await session.execute(statement)

        return [dict(row) for row in result.mappings().all()]

    @staticmethod
    async def query_users(
        session: AsyncSession,
        limit: int = 20,
    ) -> list[dict]:
        """查询用户明细。"""
        statement = (
            select(
                User.user_id,
                User.register_time,
                User.region,
            )
            .order_by(User.user_id.asc())
            .limit(limit)
        )

        result = await session.execute(statement)

        return [dict(row) for row in result.mappings().all()]
