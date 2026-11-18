"""业务分析工具。"""

from datetime import date
from decimal import Decimal
from typing import Any

from langchain_core.tools import tool

from app.database.connection import AsyncSessionLocal
from app.services.analytics_service import AnalyticsService


def _serialize_result(result: dict[str, Any]) -> dict[str, Any]:
    """将业务指标转换为适合 LLM 使用的数据格式。"""
    return {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in result.items()
    }


@tool
async def get_order_summary(
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict[str, Any]:
    """查询订单核心业务指标。

    可以查询全部订单，或者指定日期范围内的订单。
    日期格式为 YYYY-MM-DD。
    返回 GMV、有效订单量、客单价、待支付订单量、
    取消订单量、总订单量和取消率。
    """
    async with AsyncSessionLocal() as session:
        result = await AnalyticsService().get_order_summary(
            session=session,
            start_date=start_date,
            end_date=end_date,
        )

    return _serialize_result(result)
