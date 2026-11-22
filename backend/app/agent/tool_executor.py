"""业务工具注册与执行。"""

from typing import Any

from pydantic import ValidationError

from app.database.connection import AsyncSessionLocal
from app.tools.analytics_tools import create_analytics_tools
from app.tools.anomaly_tools import create_anomaly_tools
from app.tools.data_inspection_tools import create_data_inspection_tools
from app.tools.query_tools import create_query_tools


class ToolValidationError(Exception):
    """工具名称或参数验证失败。"""


def create_tool_registry(session_factory=AsyncSessionLocal):
    """创建绑定指定数据库 Session 工厂的工具注册表。"""

    registry = {}

    registry.update(create_analytics_tools(session_factory))
    registry.update(create_anomaly_tools(session_factory))
    registry.update(create_data_inspection_tools(session_factory))
    registry.update(create_query_tools(session_factory))

    expected_tools = {
        "get_order_summary",
        "analyze_trend",
        "compare_categories",
        "detect_anomalies",
        "inspect_data",
        "query_database",
    }

    if set(registry) != expected_tools:
        raise RuntimeError("业务工具注册表不完整或包含未授权工具")

    return registry


TOOL_REGISTRY = create_tool_registry()


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    registry: dict | None = None,
) -> Any:
    """验证参数并执行指定业务工具。"""

    active_registry = registry if registry is not None else TOOL_REGISTRY

    tool = active_registry.get(tool_name)

    if tool is None:
        raise ToolValidationError(f"未授权的工具：{tool_name}")

    try:
        validated_arguments = tool.args_schema.model_validate(arguments)
    except ValidationError as exc:
        raise ToolValidationError(f"工具参数验证失败：{exc}") from exc

    return await tool.ainvoke(validated_arguments.model_dump())
