"""业务分析相关的数据聚合查询。"""

from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order

VALID_ORDER_STATUSES = ("paid", "shipped", "completed")


class AnalyticsRepository:
    """业务分析数据访问层。"""

    @staticmethod
    async def get_order_summary(
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """统计订单核心指标，日期范围采用左闭右开区间。"""
        conditions = []

        if start_date is not None:
            start_datetime = datetime.combine(start_date, time.min)
            conditions.append(Order.order_time >= start_datetime)

        if end_date is not None:
            end_datetime = datetime.combine(
                end_date + timedelta(days=1),
                time.min,
            )
            conditions.append(Order.order_time < end_datetime)

        valid_order_condition = Order.order_status.in_(VALID_ORDER_STATUSES)

        statement = select(
            func.coalesce(
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
            ).label("gmv"),
            func.count(
                case(
                    (valid_order_condition, Order.order_id),
                )
            ).label("valid_order_count"),
            func.count(
                case(
                    (Order.order_status == "pending", Order.order_id),
                )
            ).label("pending_order_count"),
            func.count(
                case(
                    (Order.order_status == "cancelled", Order.order_id),
                )
            ).label("cancelled_order_count"),
            func.count(Order.order_id).label("total_order_count"),
        ).where(*conditions)

        result = (await session.execute(statement)).one()

        gmv = result.gmv or Decimal("0.00")
        valid_order_count = result.valid_order_count
        cancelled_order_count = result.cancelled_order_count
        total_order_count = result.total_order_count

        average_order_value = (
            (gmv / valid_order_count).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            if valid_order_count > 0
            else Decimal("0.00")
        )

        cancellation_rate = (
            cancelled_order_count / total_order_count if total_order_count > 0 else 0.0
        )

        return {
            "gmv": gmv,
            "valid_order_count": valid_order_count,
            "average_order_value": average_order_value,
            "pending_order_count": result.pending_order_count,
            "cancelled_order_count": cancelled_order_count,
            "total_order_count": total_order_count,
            "cancellation_rate": cancellation_rate,
        }
