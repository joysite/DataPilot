"""受限业务明细查询服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.query_repository import QueryRepository
from app.schemas.query import QueryDatabaseRequest


class QueryDatabaseService:
    """受限业务明细查询服务。"""

    async def query(
        self,
        session: AsyncSession,
        request: QueryDatabaseRequest,
    ) -> list[dict]:
        """根据经过验证的参数查询业务明细。"""

        has_order_filters = any(
            value is not None
            for value in (
                request.order_status,
                request.user_id,
                request.product_id,
            )
        )

        if request.entity != "orders" and has_order_filters:
            raise ValueError("订单筛选参数仅适用于 orders 查询")

        if request.entity == "orders":
            return await QueryRepository.query_orders(
                session=session,
                limit=request.limit,
                order_status=request.order_status,
                user_id=request.user_id,
                product_id=request.product_id,
            )

        if request.entity == "products":
            return await QueryRepository.query_products(
                session=session,
                limit=request.limit,
            )

        if request.entity == "users":
            return await QueryRepository.query_users(
                session=session,
                limit=request.limit,
            )

        raise ValueError(f"不支持的查询实体：{request.entity}")
