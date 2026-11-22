"""异常检测相关的数据聚合查询。"""

from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, Product, User
from app.repositories.analytics_repository import VALID_ORDER_STATUSES


class AnomalyRepository:
    """异常检测数据访问层。"""

    @staticmethod
    async def get_monthly_order_counts(
        session: AsyncSession,
    ) -> list[dict]:
        """统计每月全部状态的订单数量。"""

        month_expression = func.strftime(
            "%Y-%m",
            Order.order_time,
        )

        statement = (
            select(
                month_expression.label("month"),
                func.count(Order.order_id).label("order_count"),
            )
            .group_by(month_expression)
            .order_by(month_expression)
        )

        result = await session.execute(statement)

        return [
            {
                "month": row.month,
                "order_count": row.order_count,
            }
            for row in result
        ]

    @staticmethod
    async def get_monthly_gmv(
        session: AsyncSession,
    ) -> list[dict]:
        """统计每月有效订单 GMV。"""

        month_expression = func.strftime(
            "%Y-%m",
            Order.order_time,
        )

        valid_order_condition = Order.order_status.in_(VALID_ORDER_STATUSES)

        monthly_gmv = func.coalesce(
            func.sum(
                case(
                    (
                        valid_order_condition,
                        Order.order_amount,
                    ),
                    else_=Decimal("0.00"),
                )
            ),
            Decimal("0.00"),
        )

        statement = (
            select(
                month_expression.label("month"),
                monthly_gmv.label("gmv"),
            )
            .group_by(month_expression)
            .order_by(month_expression)
        )

        result = await session.execute(statement)

        return [
            {
                "month": row.month,
                "gmv": row.gmv,
            }
            for row in result
        ]

    @staticmethod
    async def get_monthly_category_gmv(
        session: AsyncSession,
    ) -> list[dict]:
        """统计每月各商品品类的有效订单 GMV。"""

        month_expression = func.strftime(
            "%Y-%m",
            Order.order_time,
        )

        statement = (
            select(
                month_expression.label("month"),
                Product.category.label("category"),
                func.sum(Order.order_amount).label("gmv"),
            )
            .join(
                Product,
                Order.product_id == Product.product_id,
            )
            .where(Order.order_status.in_(VALID_ORDER_STATUSES))
            .group_by(
                month_expression,
                Product.category,
            )
            .order_by(
                month_expression,
                Product.category,
            )
        )

        result = await session.execute(statement)

        return [
            {
                "month": row.month,
                "category": row.category,
                "gmv": row.gmv,
            }
            for row in result
        ]

    @staticmethod
    async def get_monthly_region_gmv(
        session: AsyncSession,
    ) -> list[dict]:
        """统计每月各地区的有效订单 GMV。"""

        month_expression = func.strftime(
            "%Y-%m",
            Order.order_time,
        )

        statement = (
            select(
                month_expression.label("month"),
                User.region.label("region"),
                func.sum(Order.order_amount).label("gmv"),
            )
            .join(
                User,
                Order.user_id == User.user_id,
            )
            .where(Order.order_status.in_(VALID_ORDER_STATUSES))
            .group_by(
                month_expression,
                User.region,
            )
            .order_by(
                month_expression,
                User.region,
            )
        )

        result = await session.execute(statement)

        return [
            {
                "month": row.month,
                "region": row.region,
                "gmv": row.gmv,
            }
            for row in result
        ]

    @staticmethod
    async def get_order_amount_details(
        session: AsyncSession,
    ) -> list[dict]:
        """查询有效订单金额与商品标价明细。"""

        statement = (
            select(
                Order.order_id,
                Order.order_time,
                Order.order_amount,
                Product.product_id,
                Product.price.label("product_price"),
            )
            .join(
                Product,
                Order.product_id == Product.product_id,
            )
            .where(Order.order_status.in_(VALID_ORDER_STATUSES))
            .order_by(Order.order_time)
        )

        result = await session.execute(statement)

        return [
            {
                "order_id": row.order_id,
                "order_time": row.order_time,
                "order_amount": row.order_amount,
                "product_id": row.product_id,
                "product_price": row.product_price,
            }
            for row in result
        ]
