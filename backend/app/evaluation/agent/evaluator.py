"""Agent 评测评分器。"""

from typing import Any


def _get_execution_results(actual_state: dict[str, Any]) -> list[dict[str, Any]]:
    """安全获取实际工具执行记录。"""
    results = actual_state.get("execution_results", [])
    if not isinstance(results, list):
        return []

    return [item for item in results if isinstance(item, dict)]


def _evaluate_tool_selection(
    expected_steps: list[dict[str, Any]],
    actual_results: list[dict[str, Any]],
) -> float | None:
    """按步骤位置计算工具选择准确率，并将额外步骤计入分母。"""
    if not expected_steps:
        return 1.0 if not actual_results else 0.0

    denominator = max(len(expected_steps), len(actual_results))
    correct = sum(
        1
        for index, expected in enumerate(expected_steps)
        if index < len(actual_results)
        and actual_results[index].get("tool_name") == expected.get("tool_name")
    )
    return correct / denominator


def _evaluate_arguments(
    expected_steps: list[dict[str, Any]],
    actual_results: list[dict[str, Any]],
) -> float | None:
    """比较工具名称匹配步骤的参数，忽略实际参数中的额外 None。"""
    if not expected_steps:
        return None

    denominator = max(len(expected_steps), len(actual_results))
    correct = 0

    for index, expected in enumerate(expected_steps):
        if index >= len(actual_results):
            continue

        actual = actual_results[index]

        if actual.get("tool_name") != expected.get("tool_name"):
            continue

        expected_arguments = expected.get("arguments", {})
        actual_arguments = actual.get("arguments", {})

        if not isinstance(expected_arguments, dict):
            continue

        if not isinstance(actual_arguments, dict):
            continue

        normalized_actual = {
            key: value for key, value in actual_arguments.items() if value is not None
        }

        if normalized_actual == expected_arguments:
            correct += 1

    return correct / denominator


def _evaluate_plan(
    expected_steps: list[dict[str, Any]],
    actual_steps: list[dict[str, Any]],
) -> float:
    """比较预期计划与实际生效计划。"""
    denominator = max(len(expected_steps), len(actual_steps))

    if denominator == 0:
        return 1.0

    correct = 0

    for index, expected in enumerate(expected_steps):
        if index >= len(actual_steps):
            continue

        actual = actual_steps[index]

        if not isinstance(actual, dict):
            continue

        if actual.get("step_id") != expected.get("step_id") or actual.get(
            "tool_name"
        ) != expected.get("tool_name"):
            continue

        expected_arguments = expected.get("arguments", {})
        actual_arguments = actual.get("arguments", {})

        if not isinstance(expected_arguments, dict):
            continue

        if not isinstance(actual_arguments, dict):
            continue

        normalized_actual = {
            key: value for key, value in actual_arguments.items() if value is not None
        }

        if normalized_actual == expected_arguments:
            correct += 1

    return correct / denominator


def _evaluate_answer_topics(
    expected_topics: list[str],
    actual_answer: Any,
) -> float | None:
    """使用确定性文本匹配计算回答主题覆盖率。"""
    if not expected_topics:
        return None

    if not isinstance(actual_answer, str):
        actual_answer = ""

    normalized_answer = actual_answer.casefold()

    matched = sum(
        1
        for topic in expected_topics
        if isinstance(topic, str) and topic and topic.casefold() in normalized_answer
    )

    return matched / len(expected_topics)


def _result_satisfies_fact(
    result: Any,
    required_keys: list[str],
    minimum_records: int,
) -> bool:
    """检查单个工具结果是否满足字段和记录数要求。"""
    if isinstance(result, list):
        if len(result) < minimum_records:
            return False
        return all(
            isinstance(item, dict) and all(key in item for key in required_keys)
            for item in result
        )

    if isinstance(result, dict):
        if minimum_records > 1:
            return False
        return all(key in result for key in required_keys)

    return False


def _evaluate_result_completeness(
    expected_facts: list[dict[str, Any]],
    actual_results: list[dict[str, Any]],
) -> tuple[float | None, list[dict[str, Any]]]:
    """检查预期工具结果的字段完整性。"""
    if not expected_facts:
        return None, []

    checks = []

    for fact in expected_facts:
        source_tool = fact["source_tool"]
        required_keys = fact.get("required_keys", [])
        minimum_records = fact.get("minimum_records", 0)

        matching_results = [
            item.get("result")
            for item in actual_results
            if item.get("tool_name") == source_tool
        ]

        passed = any(
            _result_satisfies_fact(
                result,
                required_keys,
                minimum_records,
            )
            for result in matching_results
        )

        checks.append(
            {
                "source_tool": source_tool,
                "passed": passed,
            }
        )

    score = sum(check["passed"] for check in checks) / len(checks)
    return score, checks


def _build_diagnostics(
    actual_state: dict[str, Any],
) -> dict[str, Any]:
    """提取真实 Agent 执行诊断信息。"""

    execution_results = _get_execution_results(actual_state)

    return {
        "actual_task_type": actual_state.get("task_type"),
        "actual_plan": actual_state.get("execution_plan"),
        "actual_steps": actual_state.get("execution_steps", []),
        "actual_execution_results": execution_results,
        "actual_answer": actual_state.get("final_answer"),
        "actual_error": {
            "error_type": actual_state.get("error_type"),
            "error": actual_state.get("error"),
        },
    }


def evaluate_case(
    case: dict[str, Any],
    actual_state: dict[str, Any],
) -> dict[str, Any]:
    """评估单条 Agent 样本并保留诊断信息。"""

    expected_steps = case.get("expected_steps", [])
    expected_facts = case.get("expected_facts", [])
    actual_results = _get_execution_results(actual_state)

    expected_task_type = case.get("expected_task_type")
    actual_task_type = actual_state.get("task_type")

    expected_answer_topics = case.get("expected_answer_topics", [])
    actual_steps = actual_state.get("execution_steps", [])

    if not isinstance(expected_steps, list):
        expected_steps = []

    if not isinstance(actual_steps, list):
        actual_steps = []

    task_type_accuracy = (
        float(actual_task_type == expected_task_type)
        if expected_task_type is not None
        else None
    )

    tool_selection_accuracy = _evaluate_tool_selection(
        expected_steps,
        actual_results,
    )
    argument_accuracy = _evaluate_arguments(
        expected_steps,
        actual_results,
    )
    result_completeness, fact_checks = _evaluate_result_completeness(
        expected_facts,
        actual_results,
    )

    plan_accuracy = _evaluate_plan(
        expected_steps,
        actual_steps,
    )

    answer_topic_coverage = _evaluate_answer_topics(
        expected_answer_topics,
        actual_state.get("final_answer"),
    )

    return {
        "case_id": case.get("case_id"),
        "metrics": {
            "task_type_accuracy": task_type_accuracy,
            "tool_selection_accuracy": tool_selection_accuracy,
            "argument_accuracy": argument_accuracy,
            "result_completeness": result_completeness,
            "plan_accuracy": plan_accuracy,
            "answer_topic_coverage": answer_topic_coverage,
        },
        "fact_checks": fact_checks,
        "diagnostics": _build_diagnostics(actual_state),
    }
