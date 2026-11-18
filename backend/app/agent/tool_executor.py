"""Agent 工具执行器。"""

from typing import Any

from app.tools.analytics_tools import get_order_summary

# 只允许执行明确注册的业务工具。
TOOL_REGISTRY = {
    get_order_summary.name: get_order_summary,
}


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    """校验并执行指定的业务工具。"""

    # 1. 检查工具白名单
    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        raise ValueError(f"不允许调用工具: {tool_name}")

    # 2. 检查参数格式
    if not isinstance(arguments, dict):
        raise ValueError("工具参数必须是 JSON 对象")

    # 3. 使用工具自身的 Pydantic Schema 校验参数
    validated_arguments = tool.args_schema.model_validate(arguments)

    # 4. 执行工具
    return await tool.ainvoke(validated_arguments.model_dump())
