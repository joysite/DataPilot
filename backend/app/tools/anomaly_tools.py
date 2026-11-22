"""异常检测工具。"""

from typing import Any

from langchain_core.tools import tool

from app.database.connection import AsyncSessionLocal
from app.services.anomaly_service import AnomalyService


def _serialize_anomalies(
    anomalies: list[Any],
) -> list[dict[str, Any]]:
    """将结构化异常结果转换为适合 LLM 使用的数据格式。"""

    return [anomaly.model_dump(mode="json") for anomaly in anomalies]


def create_anomaly_tools(session_factory=AsyncSessionLocal):
    """创建绑定指定数据库 Session 工厂的异常检测工具。"""

    @tool
    async def detect_anomalies() -> list[dict[str, Any]]:
        """检测数据库中的业务异常。

        检测品类 GMV 下降、订单量突增、地区 GMV 集中、
        整体 GMV 下降以及订单金额异常。

        返回异常类型、目标月份及对应的业务指标。
        """
        async with session_factory() as session:
            anomalies = await AnomalyService().detect_anomalies(
                session=session,
            )

        return _serialize_anomalies(anomalies)

    return {
        "detect_anomalies": detect_anomalies,
    }


_DEFAULT_TOOLS = create_anomaly_tools()

detect_anomalies = _DEFAULT_TOOLS["detect_anomalies"]
