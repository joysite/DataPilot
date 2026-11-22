"""异常检测评估指标。"""


def calculate_metrics(
    true_positive: int,
    false_positive: int,
    false_negative: int,
) -> dict[str, float]:
    """根据 TP、FP、FN 计算 Precision、Recall 和 F1。"""

    counts = (true_positive, false_positive, false_negative)

    if any(
        not isinstance(value, int) or isinstance(value, bool) or value < 0
        for value in counts
    ):
        raise ValueError("TP、FP、FN 必须是非负整数")

    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative

    precision = true_positive / precision_denominator if precision_denominator else 0.0

    recall = true_positive / recall_denominator if recall_denominator else 0.0

    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
