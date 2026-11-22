"""模型工具调用与执行计划响应解析器。"""

import json
from typing import Any

from pydantic import ValidationError

from app.agent.tool_executor import TOOL_REGISTRY

MAX_PLAN_STEPS = 5

MAX_MEMORIES_PER_TURN = 5

ALLOWED_MEMORY_TYPES = {
    "preference",
    "business_context",
    "instruction",
}


def parse_tool_call(content: str) -> dict[str, Any]:
    """解析模型返回的单个工具调用 JSON。"""

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


def parse_execution_plan(
    content: str,
    registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """解析并校验模型生成的多步骤执行计划。"""

    active_registry = registry if registry is not None else TOOL_REGISTRY

    if not isinstance(content, str) or not content.strip():
        raise ValueError("执行计划响应不能为空")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("执行计划不是合法 JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("执行计划必须是 JSON 对象")

    if set(payload) != {"steps"}:
        raise ValueError("执行计划必须且只能包含 steps 字段")

    steps = payload["steps"]

    if not isinstance(steps, list) or not steps:
        raise ValueError("steps 必须是非空列表")

    if len(steps) > MAX_PLAN_STEPS:
        raise ValueError(f"执行计划最多允许 {MAX_PLAN_STEPS} 个步骤")

    validated_steps = []

    for expected_id, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"第 {expected_id} 步必须是 JSON 对象")

        required_fields = {
            "step_id",
            "description",
            "tool_name",
            "arguments",
        }

        if set(step) != required_fields:
            raise ValueError(
                f"第 {expected_id} 步必须且只能包含 "
                "step_id、description、tool_name、arguments 字段"
            )

        step_id = step["step_id"]
        description = step["description"]
        tool_name = step["tool_name"]
        arguments = step["arguments"]

        if (
            isinstance(step_id, bool)
            or not isinstance(step_id, int)
            or step_id != expected_id
        ):
            raise ValueError(
                f"步骤编号必须从 1 开始连续递增，第 {expected_id} 步编号无效"
            )

        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"第 {expected_id} 步的 description 必须是非空字符串")

        if not isinstance(tool_name, str) or not tool_name.strip():
            raise ValueError(f"第 {expected_id} 步的 tool_name 必须是非空字符串")

        tool = active_registry.get(tool_name)

        if tool is None:
            raise ValueError(f"第 {expected_id} 步使用了未授权工具：{tool_name}")

        if not isinstance(arguments, dict):
            raise ValueError(f"第 {expected_id} 步的 arguments 必须是 JSON 对象")

        allowed_fields = set(tool.args_schema.model_fields)
        unknown_fields = set(arguments) - allowed_fields

        if unknown_fields:
            raise ValueError(
                f"第 {expected_id} 步包含未声明参数："
                f"{', '.join(sorted(unknown_fields))}"
            )

        try:
            validated_arguments = tool.args_schema.model_validate(arguments)
        except ValidationError as exc:
            raise ValueError(f"第 {expected_id} 步工具参数校验失败：{exc}") from exc

        validated_steps.append(
            {
                "step_id": step_id,
                "description": description.strip(),
                "tool_name": tool_name,
                "arguments": validated_arguments.model_dump(mode="json"),
            }
        )

    return {"steps": validated_steps}


def parse_memory_extraction(content: str) -> dict[str, Any]:
    """解析并校验模型提取的长期记忆。"""

    if not isinstance(content, str) or not content.strip():
        raise ValueError("记忆提取响应不能为空")

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("记忆提取响应不是合法 JSON") from exc

    if not isinstance(payload, dict):
        raise ValueError("记忆提取响应必须是 JSON 对象")

    if set(payload) != {"memories"}:
        raise ValueError("记忆提取响应必须且只能包含 memories 字段")

    memories = payload["memories"]

    if not isinstance(memories, list):
        raise ValueError("memories 必须是列表")

    if len(memories) > MAX_MEMORIES_PER_TURN:
        raise ValueError(f"每轮最多允许提取 {MAX_MEMORIES_PER_TURN} 条记忆")

    validated_memories = []

    for index, memory in enumerate(memories, start=1):
        if not isinstance(memory, dict):
            raise ValueError(f"第 {index} 条记忆必须是 JSON 对象")

        if set(memory) != {"memory_type", "content"}:
            raise ValueError(
                f"第 {index} 条记忆必须且只能包含 memory_type、content 字段"
            )

        memory_type = memory["memory_type"]
        content = memory["content"]

        if not isinstance(memory_type, str) or memory_type not in ALLOWED_MEMORY_TYPES:
            raise ValueError(f"第 {index} 条记忆类型无效")

        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"第 {index} 条记忆内容不能为空")

        validated_memories.append(
            {
                "memory_type": memory_type,
                "content": content.strip(),
            }
        )

    return {"memories": validated_memories}
