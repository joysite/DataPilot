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


def _serialize_result_list(
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """批量转换业务指标中的 Decimal。"""
    return [_serialize_result(result) for result in results]


def create_analytics_tools(session_factory=AsyncSessionLocal):
    """创建绑定指定数据库 Session 工厂的业务分析工具。"""

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
        async with session_factory() as session:
            result = await AnalyticsService().get_order_summary(
                session=session,
                start_date=start_date,
                end_date=end_date,
            )

        return _serialize_result(result)

    @tool
    async def analyze_trend(
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """分析指定日期范围内的月度 GMV 趋势。

        可以查询全部月份，或者指定日期范围。
        日期格式为 YYYY-MM-DD。
        返回每个月的 GMV，按月份升序排列。
        """
        async with session_factory() as session:
            result = await AnalyticsService().analyze_trend(
                session=session,
                start_date=start_date,
                end_date=end_date,
            )

        return _serialize_result_list(result)

    @tool
    async def compare_categories(
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """比较指定日期范围内各商品品类的业务表现。

        可以比较全部品类，或者指定日期范围内的品类表现。
        日期格式为 YYYY-MM-DD。
        返回品类名称、GMV、有效订单量和客单价，
        按 GMV 从高到低排列。
        """
        async with session_factory() as session:
            result = await AnalyticsService().compare_categories(
                session=session,
                start_date=start_date,
                end_date=end_date,
            )

        return _serialize_result_list(result)

    return {
        "get_order_summary": get_order_summary,
        "analyze_trend": analyze_trend,
        "compare_categories": compare_categories,
    }


_DEFAULT_TOOLS = create_analytics_tools()

get_order_summary = _DEFAULT_TOOLS["get_order_summary"]
analyze_trend = _DEFAULT_TOOLS["analyze_trend"]
compare_categories = _DEFAULT_TOOLS["compare_categories"]
