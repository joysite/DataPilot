"""LangGraph Agent 共享状态定义。"""

from typing import Annotated, Any

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """DataPilot Agent 工作流共享状态。"""

    # 对话短期记忆
    messages: Annotated[list[AnyMessage], add_messages]
    contextualized_query: str

    # 用户请求与任务理解
    user_query: str
    task_type: str

    # 执行计划
    execution_plan: str
    execution_steps: list[dict[str, Any]]
    current_step_index: int

    # 当前工具调用
    tool_name: str
    tool_arguments: dict[str, Any]
    tool_result: Any

    # 多步骤执行结果
    execution_results: list[dict[str, Any]]

    # 重试状态
    retry_count: int

    # 最终回答与错误
    final_answer: str
    error: str | None
    error_type: str | None

    # 用户身份与长期记忆
    user_id: str
    long_term_memories: list[dict[str, str]]

    # 会话身份绑定
    thread_owner_id: str
