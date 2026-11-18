"""业务分析服务。"""

from datetime import date

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
