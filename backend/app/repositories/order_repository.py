"""订单数据访问层。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.schemas.ingestion import OrderImport


class OrderRepository:
    """订单数据访问操作。"""

    @staticmethod
    async def get_existing_ids(
        session: AsyncSession,
        order_ids: list[str],
    ) -> set[str]:
        """查询已经存在的订单 ID。"""
        if not order_ids:
            return set()

        result = await session.scalars(
            select(Order.order_id).where(Order.order_id.in_(order_ids))
        )
        return set(result.all())

    @staticmethod
    async def bulk_insert(
        session: AsyncSession,
        orders: list[OrderImport],
    ) -> int:
        """批量插入订单记录，不负责提交事务。"""
        if not orders:
            return 0

        existing_ids = await OrderRepository.get_existing_ids(
            session,
            [order.order_id for order in orders],
        )

        new_orders = []
        seen_ids = set(existing_ids)

        for order in orders:
            if order.order_id in seen_ids:
                continue

            seen_ids.add(order.order_id)
            new_orders.append(
                Order(
                    order_id=order.order_id,
                    user_id=order.user_id,
                    product_id=order.product_id,
                    order_amount=order.order_amount,
                    order_status=order.order_status,
                    order_time=order.order_time,
                )
            )

        if not new_orders:
            return 0

        session.add_all(new_orders)
        await session.flush()

        return len(new_orders)
