"""LangGraph Agent 工作流定义。"""

from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    MAX_TOOL_RETRIES,
    context_resolver,
    error_handler,
    identity_validator,
    memory_extractor,
    report_generator,
    result_validator,
    task_planner,
    task_understanding,
    tool_executor,
    tool_selector,
)
from app.agent.state import AgentState


def route_on_error(state: AgentState) -> str:
    """根据错误状态决定是否进入错误处理节点。"""

    if state.get("error_type"):
        return "error_handler"

    return "continue"


def route_after_execution(state: AgentState) -> str:
    """根据工具执行结果决定继续、重试或终止。"""

    error_type = state.get("error_type")

    if error_type == "tool_execution_error":
        if state["retry_count"] <= MAX_TOOL_RETRIES:
            return "retry"

        return "error_handler"

    if error_type:
        return "error_handler"

    return "continue"


def route_after_validation(state: AgentState) -> str:
    """根据当前步骤索引决定继续执行还是生成报告。"""

    if state.get("error_type"):
        return "error_handler"

    current_step_index = state["current_step_index"]
    execution_steps = state["execution_steps"]

    if current_step_index < len(execution_steps):
        return "continue"

    return "report"


def build_agent_graph(checkpointer=None, enable_memory: bool = True):
    """创建并编译 DataPilot Agent 工作流。"""
    if not isinstance(enable_memory, bool):
        raise ValueError("enable_memory 必须是 bool")

    graph = StateGraph(AgentState)

    graph.add_node("context_resolver", context_resolver)
    graph.add_node("task_understanding", task_understanding)
    graph.add_node("task_planner", task_planner)
    graph.add_node("tool_selector", tool_selector)
    graph.add_node("tool_executor", tool_executor)
    graph.add_node("result_validator", result_validator)
    graph.add_node("report_generator", report_generator)
    graph.add_node("error_handler", error_handler)

    if enable_memory:
        graph.add_node("identity_validator", identity_validator)
        graph.add_node("memory_extractor", memory_extractor)
        graph.add_edge(START, "identity_validator")
        graph.add_conditional_edges(
            "identity_validator",
            route_on_error,
            {
                "continue": "context_resolver",
                "error_handler": END,
            },
        )
    else:
        graph.add_edge(START, "context_resolver")

    graph.add_conditional_edges(
        "task_understanding",
        route_on_error,
        {
            "continue": "task_planner",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "task_planner",
        route_on_error,
        {
            "continue": "tool_selector",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "tool_selector",
        route_on_error,
        {
            "continue": "tool_executor",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "tool_executor",
        route_after_execution,
        {
            "continue": "result_validator",
            "retry": "tool_executor",
            "error_handler": "error_handler",
        },
    )

    graph.add_conditional_edges(
        "result_validator",
        route_after_validation,
        {
            "continue": "tool_selector",
            "report": "report_generator",
            "error_handler": "error_handler",
        },
    )

    if enable_memory:
        graph.add_conditional_edges(
            "report_generator",
            route_on_error,
            {
                "continue": "memory_extractor",
                "error_handler": "error_handler",
            },
        )
        graph.add_edge("memory_extractor", END)
    else:
        graph.add_conditional_edges(
            "report_generator",
            route_on_error,
            {
                "continue": END,
                "error_handler": "error_handler",
            },
        )

    graph.add_conditional_edges(
        "context_resolver",
        route_on_error,
        {
            "continue": "task_understanding",
            "error_handler": "error_handler",
        },
    )

    graph.add_edge("error_handler", END)

    return graph.compile(checkpointer=checkpointer)
