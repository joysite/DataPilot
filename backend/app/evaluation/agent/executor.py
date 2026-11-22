"""Agent 评测执行适配器。"""

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import uuid4

from app.agent.agent import DataPilotAgent
from app.evaluation.agent.dataset import AGENT_EVALUATION_DATASET
from app.evaluation.agent.runner import evaluate_dataset


def build_evaluation_invoker(
    agent: DataPilotAgent,
) -> Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]:
    """创建绑定到隔离 Agent 的评测样本执行函数。"""

    if not isinstance(agent, DataPilotAgent):
        raise TypeError("评测执行器必须接收 DataPilotAgent 实例")

    if agent.enable_memory:
        raise ValueError("评测 Agent 必须禁用长期记忆")

    if agent.tool_registry is None:
        raise ValueError("评测 Agent 必须注入独立工具注册表")

    run_id = uuid4().hex

    async def invoke_case(case: dict[str, Any]) -> dict[str, Any]:
        """执行单条评测样本并返回完整 Graph 状态。"""

        if not isinstance(case, dict):
            raise TypeError("评测样本必须是字典")

        case_id = case.get("case_id")
        user_query = case.get("user_query")

        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("评测样本 case_id 无效")

        if not isinstance(user_query, str) or not user_query.strip():
            raise ValueError("评测样本 user_query 无效")

        return await agent.run_for_evaluation(
            user_query=user_query,
            thread_id=f"evaluation:{run_id}:{case_id}",
            user_id="evaluation",
        )

    return invoke_case


async def run_agent_evaluation(
    agent: DataPilotAgent,
    dataset: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """使用隔离 Agent 执行数据集评测并汇总结果。"""

    invoke_case = build_evaluation_invoker(agent)

    cases = dataset if dataset is not None else AGENT_EVALUATION_DATASET

    return await evaluate_dataset(
        invoke_case=invoke_case,
        dataset=cases,
    )
