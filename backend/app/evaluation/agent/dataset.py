"""DataPilot Agent 评测数据集。"""

AGENT_EVALUATION_DATASET = [
    {
        "case_id": "agent_001",
        "category": "metrics_query",
        "user_query": "查询全部订单的 GMV、有效订单量和客单价。",
        "expected_task_type": "metrics_query",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "get_order_summary",
                "arguments": {},
            }
        ],
        "expected_facts": [
            {
                "source_tool": "get_order_summary",
                "required_keys": [
                    "gmv",
                    "valid_order_count",
                    "average_order_value",
                ],
            }
        ],
        "expected_answer_topics": [
            "GMV",
            "有效订单量",
            "客单价",
        ],
    },
    {
        "case_id": "agent_002",
        "category": "trend_analysis",
        "user_query": "分析 2026 年 1 月至 6 月的月度 GMV 趋势。",
        "expected_task_type": "trend_analysis",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "analyze_trend",
                "arguments": {
                    "start_date": "2026-01-01",
                    "end_date": "2026-06-30",
                },
            }
        ],
        "expected_facts": [
            {
                "source_tool": "analyze_trend",
                "required_keys": ["month", "gmv"],
                "minimum_records": 1,
            }
        ],
        "expected_answer_topics": [
            "月度 GMV",
            "变化趋势",
        ],
    },
    {
        "case_id": "agent_003",
        "category": "anomaly_detection",
        "user_query": "对全部历史订单进行业务异常检测。",
        "expected_task_type": "anomaly_detection",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "detect_anomalies",
                "arguments": {},
            }
        ],
        "expected_facts": [
            {
                "source_tool": "detect_anomalies",
                "required_keys": [
                    "anomaly_type",
                    "target_month",
                ],
                "minimum_records": 1,
            }
        ],
        "expected_answer_topics": [
            "异常总数",
            "异常类型",
            "涉及月份",
        ],
    },
    {
        "case_id": "agent_004",
        "category": "category_comparison",
        "user_query": "比较全部商品品类的 GMV 和有效订单量。",
        "expected_task_type": "category_comparison",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "compare_categories",
                "arguments": {},
            }
        ],
        "expected_facts": [
            {
                "source_tool": "compare_categories",
                "required_keys": [
                    "category",
                    "gmv",
                    "valid_order_count",
                    "average_order_value",
                ],
                "minimum_records": 1,
            }
        ],
        "expected_answer_topics": [
            "品类 GMV",
            "有效订单量",
        ],
    },
    {
        "case_id": "agent_005",
        "category": "data_inspection",
        "user_query": "检查全部业务表的数据质量和完整性。",
        "expected_task_type": "data_inspection",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "inspect_data",
                "arguments": {},
            }
        ],
        "expected_facts": [
            {
                "source_tool": "inspect_data",
                "required_keys": [
                    "table_counts",
                    "table_details",
                    "integrity",
                    "import_history",
                ],
            }
        ],
        "expected_answer_topics": [
            "数据量",
            "数据质量",
            "数据完整性",
        ],
    },
    {
        "case_id": "agent_006",
        "category": "data_inspection",
        "user_query": "检查 orders 表的数据质量。",
        "expected_task_type": "data_inspection",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "inspect_data",
                "arguments": {
                    "table_name": "orders",
                },
            }
        ],
        "expected_facts": [
            {
                "source_tool": "inspect_data",
                "required_keys": [
                    "table_counts",
                    "table_details",
                    "integrity",
                    "import_history",
                ],
            }
        ],
        "expected_answer_topics": [
            "orders 表",
            "数据质量",
        ],
    },
    {
        "case_id": "agent_007",
        "category": "detail_query",
        "user_query": "查询最近 10 笔订单明细。",
        "expected_task_type": "detail_query",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "query_database",
                "arguments": {
                    "entity": "orders",
                    "limit": 10,
                },
            }
        ],
        "expected_facts": [
            {
                "source_tool": "query_database",
                "required_keys": [],
                "minimum_records": 1,
            }
        ],
        "expected_answer_topics": [
            "订单明细",
            "订单信息",
        ],
    },
    {
        "case_id": "agent_008",
        "category": "detail_query",
        "user_query": "查询最近 10 笔已取消订单。",
        "expected_task_type": "detail_query",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "query_database",
                "arguments": {
                    "entity": "orders",
                    "limit": 10,
                    "order_status": "cancelled",
                },
            }
        ],
        "expected_facts": [
            {
                "source_tool": "query_database",
                "required_keys": [],
                "minimum_records": 1,
            }
        ],
        "expected_answer_topics": [
            "已取消订单",
            "订单明细",
        ],
    },
    {
        "case_id": "agent_009",
        "category": "multi_step",
        "user_query": "先查询全部订单核心指标，再分析全部历史月份的 GMV 趋势。",
        "expected_task_type": "trend_analysis",
        "expected_steps": [
            {
                "step_id": 1,
                "tool_name": "get_order_summary",
                "arguments": {},
            },
            {
                "step_id": 2,
                "tool_name": "analyze_trend",
                "arguments": {},
            },
        ],
        "expected_facts": [
            {
                "source_tool": "get_order_summary",
                "required_keys": [
                    "gmv",
                    "valid_order_count",
                    "average_order_value",
                ],
            },
            {
                "source_tool": "analyze_trend",
                "required_keys": ["month", "gmv"],
                "minimum_records": 1,
            },
        ],
        "expected_answer_topics": [
            "订单核心指标",
            "月度 GMV 趋势",
        ],
    },
    {
        "case_id": "agent_010",
        "category": "unsupported",
        "user_query": "帮我预测下个月每个商品的销量。",
        "expected_task_type": "general_query",
        "expected_steps": [],
        "expected_facts": [],
        "expected_answer_topics": [
            "当前不支持",
        ],
    },
]
