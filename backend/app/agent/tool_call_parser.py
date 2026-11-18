"""模型工具调用响应解析器。"""

import json
from typing import Any


def parse_tool_call(content: str) -> dict[str, Any]:
    """解析模型返回的工具调用 JSON。"""

    if not isinstance(content, str) or not content.strip():
        raise ValueError("模型响应不能为空")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("模型响应不是合法 JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("模型响应必须是 JSON 对象")

    tool_name = payload.get("name")
    arguments = payload.get("arguments")

    if not isinstance(tool_name, str) or not tool_name.strip():
        raise ValueError("工具名称必须是非空字符串")

    if not isinstance(arguments, dict):
        raise ValueError("工具参数必须是 JSON 对象")

    return {
        "name": tool_name,
        "arguments": arguments,
    }
