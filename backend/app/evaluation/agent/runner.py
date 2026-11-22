"""Agent 评测结果汇总。"""

from collections.abc import Awaitable, Callable
from typing import Any

from app.evaluation.agent.dataset import AGENT_EVALUATION_DATASET
from app.evaluation.agent.evaluator import evaluate_case

METRIC_NAMES = (
    "task_type_accuracy",
    "plan_accuracy",
    "tool_selection_accuracy",
    "argument_accuracy",
    "result_completeness",
    "answer_topic_coverage",
)


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    """汇总多条样本的评分结果。"""
    metric_values: dict[str, list[float]] = {name: [] for name in METRIC_NAMES}
    passed_case_ids = []
    failed_case_ids = []

    for result in results:
        metrics = result.get("metrics", {})
        applicable_scores = []

        for name in METRIC_NAMES:
            score = metrics.get(name)

            if score is None:
                continue

            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise ValueError(f"指标 {name} 必须是数字或 None")

            if not 0.0 <= score <= 1.0:
                raise ValueError(f"指标 {name} 必须在 0 到 1 之间")

            metric_values[name].append(float(score))
            applicable_scores.append(float(score))

        case_id = result.get("case_id")

        if applicable_scores and all(score == 1.0 for score in applicable_scores):
            passed_case_ids.append(case_id)
        else:
            failed_case_ids.append(case_id)

    metric_summary = {}

    for name, values in metric_values.items():
        metric_summary[name] = {
            "average": (sum(values) / len(values) if values else None),
            "evaluated_cases": len(values),
        }

    total_cases = len(results)
    passed_cases = len(passed_case_ids)

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": total_cases - passed_cases,
        "pass_rate": (passed_cases / total_cases if total_cases else 0.0),
        "passed_case_ids": passed_case_ids,
        "failed_case_ids": failed_case_ids,
        "metrics": metric_summary,
        "case_results": results,
    }


async def evaluate_dataset(
    invoke_case: Callable[
        [dict[str, Any]],
        Awaitable[dict[str, Any]],
    ],
    dataset: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """执行 Agent 评测并隔离单条样本异常。"""

    cases = dataset if dataset is not None else AGENT_EVALUATION_DATASET
    results = []

    for case in cases:
        actual_state = {}

        try:
            candidate_state = await invoke_case(case)

            if not isinstance(candidate_state, dict):
                raise TypeError("评测执行函数必须返回字典状态")

            actual_state = candidate_state
            result = evaluate_case(case, actual_state)

        except Exception as exc:
            result = evaluate_case(case, actual_state)

            result["runner_error"] = {
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

        results.append(result)

    return summarize_results(results)
