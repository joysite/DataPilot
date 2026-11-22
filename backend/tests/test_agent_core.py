import json

import pytest

from app.agent.tool_call_parser import (
    parse_execution_plan,
    parse_memory_extraction,
    parse_tool_call,
)
from app.agent.tool_executor import TOOL_REGISTRY
from app.evaluation.metrics import calculate_metrics

# ============================================================
# 1. 单工具调用解析
# ============================================================


def test_parse_tool_call_success():
    result = parse_tool_call(
        '{"name": "query_database", "arguments": {"entity": "orders"}}'
    )
    assert result == {
        "name": "query_database",
        "arguments": {"entity": "orders"},
    }


@pytest.mark.parametrize(
    "content",
    [
        "",
        "   ",
        "{invalid json}",
        "[]",
        '"text"',
        "null",
        "123",
    ],
)
def test_parse_tool_call_rejects_invalid_content(content):
    with pytest.raises(ValueError):
        parse_tool_call(content)


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "arguments": {}},
        {"name": 123, "arguments": {}},
        {"name": "query_database", "arguments": []},
        {"name": "query_database", "arguments": None},
    ],
)
def test_parse_tool_call_rejects_invalid_fields(payload):
    with pytest.raises(ValueError):
        parse_tool_call(json.dumps(payload))


# ============================================================
# 2. 多步骤执行计划解析
# ============================================================


def make_step(step_id=1, tool_name="query_database", arguments=None):
    if arguments is None:
        arguments = {"entity": "orders"}

    return {
        "step_id": step_id,
        "description": " 查询订单 ",
        "tool_name": tool_name,
        "arguments": arguments,
    }


def make_plan(*steps):
    return json.dumps({"steps": list(steps)}, ensure_ascii=False)


def test_parse_execution_plan_success():
    result = parse_execution_plan(
        make_plan(
            make_step(
                tool_name="query_database",
                arguments={"entity": "orders", "limit": 10},
            ),
            make_step(
                step_id=2,
                tool_name="inspect_data",
                arguments={"table_name": "products"},
            ),
        )
    )

    assert len(result["steps"]) == 2
    assert result["steps"][0]["step_id"] == 1
    assert result["steps"][0]["description"] == "查询订单"
    assert result["steps"][0]["arguments"]["entity"] == "orders"
    assert result["steps"][1]["tool_name"] == "inspect_data"


def test_parse_execution_plan_supports_empty_schema():
    result = parse_execution_plan(
        make_plan(
            make_step(
                tool_name="detect_anomalies",
                arguments={},
            )
        )
    )
    assert result["steps"][0]["arguments"] == {}


def test_parse_execution_plan_supports_optional_date_arguments():
    result = parse_execution_plan(
        make_plan(
            make_step(
                tool_name="analyze_trend",
                arguments={
                    "start_date": "2025-01-01",
                    "end_date": "2025-01-31",
                },
            )
        )
    )
    assert result["steps"][0]["arguments"]["start_date"] == "2025-01-01"


@pytest.mark.parametrize(
    "content",
    [
        "",
        "not json",
        "[]",
        "{}",
        '{"steps": []}',
        '{"steps": [], "extra": true}',
    ],
)
def test_parse_execution_plan_rejects_invalid_structure(content):
    with pytest.raises(ValueError):
        parse_execution_plan(content)


def test_parse_execution_plan_rejects_more_than_five_steps():
    steps = [make_step(step_id=index) for index in range(1, 7)]
    with pytest.raises(ValueError, match="最多允许"):
        parse_execution_plan(make_plan(*steps))


@pytest.mark.parametrize("step_id", [0, 2, -1, True, "1"])
def test_parse_execution_plan_rejects_invalid_step_id(step_id):
    with pytest.raises(ValueError, match="步骤编号"):
        parse_execution_plan(make_plan(make_step(step_id=step_id)))


def test_parse_execution_plan_rejects_unauthorized_tool():
    with pytest.raises(ValueError, match="未授权工具"):
        parse_execution_plan(make_plan(make_step(tool_name="delete_database")))


def test_parse_execution_plan_rejects_unknown_argument():
    with pytest.raises(ValueError, match="未声明参数"):
        parse_execution_plan(
            make_plan(
                make_step(
                    arguments={
                        "entity": "orders",
                        "unexpected": "value",
                    }
                )
            )
        )


def test_parse_execution_plan_rejects_invalid_enum():
    with pytest.raises(ValueError, match="参数校验失败"):
        parse_execution_plan(make_plan(make_step(arguments={"entity": "payments"})))


def test_parse_execution_plan_rejects_missing_required_argument():
    with pytest.raises(ValueError, match="参数校验失败"):
        parse_execution_plan(make_plan(make_step(arguments={})))


def test_parse_execution_plan_rejects_invalid_date():
    with pytest.raises(ValueError, match="参数校验失败"):
        parse_execution_plan(
            make_plan(
                make_step(
                    tool_name="analyze_trend",
                    arguments={"start_date": "not-a-date"},
                )
            )
        )


def test_parse_execution_plan_rejects_extra_step_field():
    step = make_step()
    step["extra"] = "unexpected"

    with pytest.raises(ValueError, match="只能包含"):
        parse_execution_plan(make_plan(step))


def test_parse_execution_plan_uses_custom_registry():
    with pytest.raises(ValueError, match="未授权工具"):
        parse_execution_plan(
            make_plan(make_step()),
            registry={},
        )


# ============================================================
# 3. 长期记忆解析
# ============================================================


def test_parse_memory_extraction_success():
    result = parse_memory_extraction(
        json.dumps(
            {
                "memories": [
                    {
                        "memory_type": "preference",
                        "content": "  优先使用中文回答  ",
                    },
                    {
                        "memory_type": "instruction",
                        "content": "按步骤推进项目",
                    },
                ]
            },
            ensure_ascii=False,
        )
    )

    assert result == {
        "memories": [
            {
                "memory_type": "preference",
                "content": "优先使用中文回答",
            },
            {
                "memory_type": "instruction",
                "content": "按步骤推进项目",
            },
        ]
    }


def test_parse_memory_extraction_allows_empty_list():
    assert parse_memory_extraction('{"memories": []}') == {"memories": []}


@pytest.mark.parametrize(
    "content",
    [
        "",
        "invalid json",
        "[]",
        "{}",
        '{"memories": [], "extra": true}',
    ],
)
def test_parse_memory_extraction_rejects_invalid_structure(content):
    with pytest.raises(ValueError):
        parse_memory_extraction(content)


def test_parse_memory_extraction_rejects_more_than_five():
    memories = [
        {"memory_type": "preference", "content": f"memory {index}"}
        for index in range(6)
    ]

    with pytest.raises(ValueError, match="最多允许"):
        parse_memory_extraction(json.dumps({"memories": memories}))


@pytest.mark.parametrize(
    "memory",
    [
        {"memory_type": "unknown", "content": "内容"},
        {"memory_type": "preference", "content": ""},
        {"memory_type": "preference", "content": "   "},
        {"memory_type": "preference", "content": 123},
        {"memory_type": "preference"},
        {"memory_type": "preference", "content": "内容", "extra": 1},
        "not an object",
    ],
)
def test_parse_memory_extraction_rejects_invalid_memory(memory):
    with pytest.raises(ValueError):
        parse_memory_extraction(json.dumps({"memories": [memory]}))


# ============================================================
# 4. 异常检测指标
# ============================================================


def test_calculate_metrics_normal_case():
    result = calculate_metrics(
        true_positive=8,
        false_positive=2,
        false_negative=2,
    )

    assert result["precision"] == pytest.approx(0.8)
    assert result["recall"] == pytest.approx(0.8)
    assert result["f1"] == pytest.approx(0.8)


def test_calculate_metrics_no_predictions():
    result = calculate_metrics(0, 0, 5)
    assert result == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }


def test_calculate_metrics_no_ground_truth():
    result = calculate_metrics(0, 5, 0)
    assert result["precision"] == 0.0
    assert result["recall"] == 0.0
    assert result["f1"] == 0.0


def test_calculate_metrics_all_zero():
    assert calculate_metrics(0, 0, 0) == {
        "precision": 0.0,
        "recall": 0.0,
        "f1": 0.0,
    }


@pytest.mark.parametrize(
    "counts",
    [
        (-1, 0, 0),
        (0, -1, 0),
        (0, 0, -1),
        (1.5, 0, 0),
        (0, True, 0),
    ],
)
def test_calculate_metrics_rejects_invalid_counts(counts):
    with pytest.raises(ValueError):
        calculate_metrics(*counts)


# ============================================================
# 5. 注册表基本完整性
# ============================================================


def test_tool_registry_contains_six_expected_tools():
    assert set(TOOL_REGISTRY) == {
        "get_order_summary",
        "analyze_trend",
        "compare_categories",
        "detect_anomalies",
        "inspect_data",
        "query_database",
    }
