"""业务分析服务。"""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    """业务分析服务。"""

    async def get_order_summary(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """获取指定日期范围内的订单核心指标。"""
        if start_date and end_date and start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")

        return await AnalyticsRepository.get_order_summary(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

    async def analyze_trend(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """分析指定日期范围内的月度 GMV 趋势。"""

        if start_date and end_date and start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")

        return await AnalyticsRepository.get_monthly_gmv(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

    async def compare_categories(
        self,
        session: AsyncSession,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict]:
        """比较指定日期范围内各商品品类的业务表现。"""

        if start_date and end_date and start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")

        rows = await AnalyticsRepository.compare_categories(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

        results = []

        for row in rows:
            gmv = row["gmv"]
            valid_order_count = row["valid_order_count"]

            average_order_value = (
                (gmv / valid_order_count).quantize(Decimal("0.01"))
                if valid_order_count > 0
                else Decimal("0.00")
            )

            results.append(
                {
                    **row,
                    "average_order_value": average_order_value,
                }
            )

        return results
