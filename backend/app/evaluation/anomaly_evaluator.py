"""异常检测评估器。"""

import json
from pathlib import Path
from typing import Any

from app.evaluation.metrics import calculate_metrics

# Ground Truth 类型 -> AnomalyService 检测结果类型
ANOMALY_TYPE_MAPPING = {
    "category_sales_drop": "category_gmv_drop",
    "order_count_spike": "order_count_spike",
    "regional_sales_concentration": "region_gmv_concentration",
    "overall_sales_drop": "overall_gmv_drop",
    "order_amount_outliers": "abnormal_order_amount",
}


class AnomalyEvaluator:
    """异常检测评估器。"""

    def __init__(self, ground_truth_path: Path) -> None:
        self.ground_truth_path = ground_truth_path

    def load_ground_truth(self) -> list[dict[str, Any]]:
        """加载并检查 Ground Truth 标签。"""

        if not self.ground_truth_path.is_file():
            raise FileNotFoundError(
                f"Ground Truth 文件不存在: {self.ground_truth_path}"
            )

        try:
            data = json.loads(self.ground_truth_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Ground Truth JSON 格式无效") from exc

        if not isinstance(data, dict):
            raise ValueError("Ground Truth 根节点必须是 JSON 对象")

        anomalies = data.get("anomalies")

        if not isinstance(anomalies, list):
            raise ValueError("Ground Truth anomalies 必须是数组")

        anomaly_ids = []

        for item in anomalies:
            if not isinstance(item, dict):
                raise ValueError("每条 Ground Truth 必须是 JSON 对象")

            anomaly_id = item.get("anomaly_id")
            anomaly_type = item.get("anomaly_type")

            if not isinstance(anomaly_id, str) or not anomaly_id.strip():
                raise ValueError("Ground Truth anomaly_id 无效")

            if anomaly_type not in ANOMALY_TYPE_MAPPING:
                raise ValueError(f"不支持的 Ground Truth 异常类型: {anomaly_type}")

            anomaly_ids.append(anomaly_id)

        if len(anomaly_ids) != len(set(anomaly_ids)):
            raise ValueError("Ground Truth 存在重复 anomaly_id")

        return anomalies

    def match_events(
        self,
        detections: list[Any],
    ) -> dict[str, Any]:
        """将检测结果与 Ground Truth 进行事件级匹配。"""

        ground_truth = self.load_ground_truth()

        detection_items = []

        for item in detections:
            if isinstance(item, dict):
                detection_items.append(item)
            elif hasattr(item, "model_dump"):
                detection_items.append(item.model_dump(mode="json"))
            else:
                raise TypeError("检测结果必须是字典或 Pydantic 模型")

        matched_events = []
        missed_events = []
        matched_detection_indexes = set()

        for label in ground_truth:
            expected_type = ANOMALY_TYPE_MAPPING[label["anomaly_type"]]

            matches = []

            for index, detection in enumerate(detection_items):
                if detection.get("anomaly_type") != expected_type:
                    continue

                if detection.get("target_month") != label["target_month"]:
                    continue

                if label["anomaly_type"] == "category_sales_drop":
                    if detection.get("category") != label["target_category"]:
                        continue

                elif label["anomaly_type"] == "regional_sales_concentration":
                    if detection.get("region") != label["target_region"]:
                        continue

                matches.append(detection)
                matched_detection_indexes.add(index)

            if matches:
                matched_events.append(
                    {
                        "anomaly_id": label["anomaly_id"],
                        "anomaly_type": label["anomaly_type"],
                        "target_month": label["target_month"],
                        "detection_count": len(matches),
                        "detections": matches,
                    }
                )
            else:
                missed_events.append(label)

        total = len(ground_truth)
        matched = len(matched_events)

        return {
            "total_ground_truth": total,
            "matched": matched,
            "missed": len(missed_events),
            "recall": matched / total if total else 0.0,
            "matched_events": matched_events,
            "missed_events": missed_events,
            "unreviewed_detections": [
                detection
                for index, detection in enumerate(detection_items)
                if index not in matched_detection_indexes
            ],
        }

    def evaluate_order_level(
        self,
        detections: list[Any],
    ) -> dict[str, Any]:
        """评估 A05 异常订单的识别效果。"""

        ground_truth = self.load_ground_truth()

        label = next(
            (item for item in ground_truth if item["anomaly_id"] == "A05"),
            None,
        )

        if label is None:
            raise ValueError("Ground Truth 缺少 A05 标签")

        expected_ids = label.get("affected_order_ids")

        if not isinstance(expected_ids, list) or not all(
            isinstance(order_id, str) and order_id.strip() for order_id in expected_ids
        ):
            raise ValueError("A05 affected_order_ids 格式无效")

        expected_order_ids = set(expected_ids)

        detected_order_ids = set()

        for item in detections:
            if isinstance(item, dict):
                detection = item
            elif hasattr(item, "model_dump"):
                detection = item.model_dump(mode="json")
            else:
                raise TypeError("检测结果必须是字典或 Pydantic 模型")

            if (
                detection.get("anomaly_type")
                != ANOMALY_TYPE_MAPPING[label["anomaly_type"]]
                or detection.get("target_month") != label["target_month"]
            ):
                continue

            order_id = detection.get("order_id")

            if isinstance(order_id, str) and order_id.strip():
                detected_order_ids.add(order_id)

        matched_ids = expected_order_ids & detected_order_ids
        false_positive_ids = detected_order_ids - expected_order_ids
        false_negative_ids = expected_order_ids - detected_order_ids

        true_positive = len(matched_ids)
        false_positive = len(false_positive_ids)
        false_negative = len(false_negative_ids)

        metrics = calculate_metrics(
            true_positive=true_positive,
            false_positive=false_positive,
            false_negative=false_negative,
        )

        return {
            "anomaly_id": "A05",
            "target_month": label["target_month"],
            "true_positive": true_positive,
            "false_positive": false_positive,
            "false_negative": false_negative,
            **metrics,
            "matched_order_ids": sorted(matched_ids),
            "false_positive_order_ids": sorted(false_positive_ids),
            "false_negative_order_ids": sorted(false_negative_ids),
        }

    def evaluate(
        self,
        detections: list[Any],
    ) -> dict[str, Any]:
        """执行完整异常检测评估并生成统一报告数据。"""

        event_result = self.match_events(detections)
        order_result = self.evaluate_order_level(detections)

        return {
            "event_level": event_result,
            "order_level": order_result,
            "unreviewed_detections": (event_result["unreviewed_detections"]),
        }

    def save_report(
        self,
        report: dict[str, Any],
        output_path: Path,
    ) -> None:
        """将评估报告保存为 JSON 文件。"""

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            output_path.write_text(
                json.dumps(
                    report,
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            raise OSError(f"评估报告保存失败: {output_path}") from exc
