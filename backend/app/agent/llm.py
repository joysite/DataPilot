"""本地大语言模型初始化与工具调用生成。"""

import json

from langchain_ollama import ChatOllama

from app.agent.tool_executor import TOOL_REGISTRY
from app.core.config import settings


def create_chat_model() -> ChatOllama:
    """创建普通 Ollama 对话模型。"""
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.ollama_temperature,
    )


def create_tool_call_model() -> ChatOllama:
    """创建 JSON 模式的工具调用模型。"""
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=settings.ollama_temperature,
        format="json",
    )


def build_tool_call_prompt() -> str:
    """构建包含工具定义的系统提示词。"""

    tools = []

    for tool in TOOL_REGISTRY.values():
        tools.append(
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.model_json_schema(),
            }
        )

    tool_definitions = json.dumps(
        tools,
        ensure_ascii=False,
    )

    return f"""
你是 DataPilot 电商数据分析助手。

你需要根据用户的问题，判断是否调用已提供的业务工具。

可用工具定义：
{tool_definitions}

调用规则：
1. 只能选择上述工具。
2. 不允许编造工具名称或参数。
3. 日期参数使用 YYYY-MM-DD 格式。
4. 必须严格返回 JSON 对象。
5. 不要输出 Markdown、代码块或额外解释。
6. JSON 必须包含 name 和 arguments 两个字段。

输出格式：
{{
    "name": "工具名称",
    "arguments": {{
        "参数名称": "参数值"
    }}
}}
"""


async def generate_tool_call(user_query: str) -> str:
    """根据用户问题生成工具调用 JSON。"""

    if not user_query.strip():
        raise ValueError("用户问题不能为空")

    model = create_tool_call_model()

    response = await model.ainvoke(
        [
            ("system", build_tool_call_prompt()),
            ("human", user_query),
        ]
    )

    if not isinstance(response.content, str):
        raise ValueError("模型响应必须是文本")

    return response.content
