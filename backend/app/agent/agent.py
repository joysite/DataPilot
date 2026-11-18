"""DataPilot Agent 主流程。"""

import json
from typing import Any

from app.agent.llm import (
    create_chat_model,
    generate_tool_call,
)
from app.agent.tool_call_parser import parse_tool_call
from app.agent.tool_executor import execute_tool


class DataPilotAgent:
    """DataPilot 业务分析 Agent。"""

    async def run(self, user_query: str) -> dict[str, Any]:
        """执行工具调用并生成最终回答。"""

        if not isinstance(user_query, str) or not user_query.strip():
            return {
                "success": False,
                "error": "invalid_input",
                "message": "用户问题不能为空",
            }

        # 1. 模型生成工具调用请求
        try:
            model_response = await generate_tool_call(user_query)
        except Exception:
            return {
                "success": False,
                "error": "model_generation_error",
                "message": "模型生成工具调用请求失败",
            }

        # 2. 解析模型响应
        try:
            tool_call = parse_tool_call(model_response)
        except ValueError:
            return {
                "success": False,
                "error": "tool_call_parse_error",
                "message": "模型返回的工具调用格式无效",
            }

        # 3. 执行工具
        try:
            tool_result = await execute_tool(
                tool_name=tool_call["name"],
                arguments=tool_call["arguments"],
            )
        except ValueError:
            return {
                "success": False,
                "error": "tool_call_validation_error",
                "message": "工具名称或参数校验失败",
            }
        except Exception:
            return {
                "success": False,
                "error": "tool_execution_error",
                "message": "工具执行失败",
            }

        # 4. 将工具结果交还给模型
        result_json = json.dumps(
            tool_result,
            ensure_ascii=False,
        )

        try:
            model = create_chat_model()

            response = await model.ainvoke(
                [
                    (
                        "system",
                        (
                            "你是 DataPilot 电商业务分析助手。"
                            "请根据提供的工具执行结果回答用户问题。"
                            "所有业务指标必须以工具结果为准，"
                            "不得编造、修改或推测数据。"
                            "金额单位为人民币元。"
                            "取消率请转换为百分比展示，"
                            "保留两位小数。"
                            "使用简洁、清晰的中文回答。"
                        ),
                    ),
                    (
                        "human",
                        (f"用户问题：{user_query}\n\n工具执行结果：{result_json}"),
                    ),
                ]
            )

            if not isinstance(response.content, str):
                raise ValueError("模型最终回答必须是文本")

        except Exception:
            return {
                "success": False,
                "error": "answer_generation_error",
                "message": "业务数据查询成功，但自然语言回答生成失败",
                "tool_name": tool_call["name"],
                "arguments": tool_call["arguments"],
                "result": tool_result,
            }

        # 5. 返回完整结果
        return {
            "success": True,
            "tool_name": tool_call["name"],
            "arguments": tool_call["arguments"],
            "result": tool_result,
            "answer": response.content,
        }
