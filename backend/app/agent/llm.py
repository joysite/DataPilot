"""本地大语言模型初始化与工具调用生成。"""

import json
from typing import Any

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


def build_tool_call_prompt(
    registry: dict[str, Any] | None = None,
) -> str:
    """构建包含指定工具注册表定义的系统提示词。"""

    active_registry = registry if registry is not None else TOOL_REGISTRY

    tools = []

    for tool in active_registry.values():
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

你的任务是理解用户的业务问题，并选择最合适的业务工具。

可用工具定义：
{tool_definitions}

工具选择规则：

1. 用户需要查询整体订单指标、GMV、有效订单量、
   客单价、待支付订单量、取消订单量或取消率时，
   选择 get_order_summary。

2. 用户需要分析月度 GMV 趋势、查看不同月份的 GMV
   变化时，选择 analyze_trend。

3. 用户需要比较不同商品品类的 GMV、
   有效订单量或客单价时，
   选择 compare_categories。

4. 用户需要检查、发现、识别或汇总业务异常时，
   选择 detect_anomalies。

5. 用户需要检查数据集概况、数据表结构、字段类型、
   NULL 值数量、外键完整性或数据导入历史时，
   选择 inspect_data。

   如果用户指定 users、products 或 orders 表，
   将对应表名传入 table_name 参数。
   如果用户要求检查整个数据集，不传 table_name 参数。

6. 用户需要查询具体的订单、商品或用户业务明细时，
   选择 query_database。

   - 查询订单明细、最近订单或订单列表时，
     entity 设置为 "orders"。
   - 查询商品明细、商品列表时，
     entity 设置为 "products"。
   - 查询用户明细、用户列表时，
     entity 设置为 "users"。

   只有用户明确指定订单状态时，才传入 order_status。
   只有用户明确提供用户 ID 时，才传入 user_id。
   只有用户明确提供商品 ID 时，才传入 product_id。

   用户指定返回数量时，将数量传入 limit；
   未指定时使用默认值 20，最大不能超过 100。

   不得为 query_database 编造日期筛选、
   排序字段或其他 Schema 未定义的参数。

   注意区分：
   - 查询 GMV、订单量、客单价等统计指标，
     使用 get_order_summary。
   - 查询具体订单记录，使用 query_database。
   - 检查表结构、NULL 值和数据完整性，
     使用 inspect_data。

7. 不得将异常检测请求错误地交给订单指标查询工具。

8. 只能选择上述工具，不允许编造工具名称。

9. 工具参数必须符合对应 JSON Schema。
   不允许编造参数或添加 Schema 未定义的字段。

10. 如果用户指定日期范围，日期使用 YYYY-MM-DD 格式。
    如果用户没有指定日期范围，使用工具默认参数。

11. 当前每次只允许调用一个工具。

12. 必须严格返回 JSON 对象，不得输出 Markdown、
    代码块或额外解释。

输出格式：
{{
    "name": "工具名称",
    "arguments": {{
        "参数名称": "参数值"
    }}
}}
"""


def build_execution_plan_prompt(
    registry: dict[str, Any] | None = None,
) -> str:
    """构建包含指定工具注册表定义的多步骤执行计划提示词。"""

    active_registry = registry if registry is not None else TOOL_REGISTRY

    tools = []

    for tool in active_registry.values():
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

你的任务是理解用户的业务问题，并制定合理的业务工具执行计划。

可用工具定义：
{tool_definitions}

计划制定规则：

1. 只能使用上述工具，禁止编造工具名称。

2. 根据用户问题判断需要执行哪些操作。
   如果一个工具就能完成任务，只生成一个步骤。
   如果任务需要多个工具配合，生成多个有明确先后顺序的步骤。

3. 每个步骤只能调用一个工具。

4. 优先选择能够直接回答用户问题的工具，
   不要添加无关步骤，不要重复执行相同操作。

5. 后续步骤可以利用前面步骤获取的数据进行分析，
   但 arguments 必须符合对应工具的 JSON Schema。
   不允许编造前置步骤尚未提供的数据。

6. 工具参数必须符合对应 JSON Schema。
   不允许添加 Schema 未定义的字段。

7. 如果用户指定日期范围，日期使用 YYYY-MM-DD 格式。
   如果用户没有指定日期范围，使用工具默认参数。

8. 异常检测工具当前只支持全历史数据检测，
   不要为其编造日期筛选参数。

9. 最多生成 5 个步骤，step_id 必须从 1 开始连续递增。

10. 每个步骤的 description 应简洁说明该步骤的业务目的。

11. 必须严格返回 JSON 对象，不得输出 Markdown、
    代码块或额外解释。

输出格式：
{{
    "steps": [
        {{
            "step_id": 1,
            "description": "步骤说明",
            "tool_name": "工具名称",
            "arguments": {{}}
        }}
    ]
}}
"""


async def generate_execution_plan(
    user_query: str,
    registry: dict[str, Any] | None = None,
) -> str:
    """根据用户问题和指定工具注册表生成多步骤执行计划 JSON。"""

    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError("用户问题不能为空")

    model = create_tool_call_model()

    response = await model.ainvoke(
        [
            ("system", build_execution_plan_prompt(registry)),
            ("human", user_query),
        ]
    )

    if not isinstance(response.content, str):
        raise ValueError("模型响应必须是文本")

    return response.content


async def generate_tool_call(
    user_query: str,
    registry: dict[str, Any] | None = None,
) -> str:
    """根据用户问题和指定工具注册表生成工具调用 JSON。"""

    if not isinstance(user_query, str) or not user_query.strip():
        raise ValueError("用户问题不能为空")

    model = create_tool_call_model()

    response = await model.ainvoke(
        [
            ("system", build_tool_call_prompt(registry)),
            ("human", user_query),
        ]
    )

    if not isinstance(response.content, str):
        raise ValueError("模型响应必须是文本")

    return response.content
