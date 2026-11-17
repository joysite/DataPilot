"""DataPilot 业务异常数据注入器。"""

import csv
import json
import random
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
LABELS_FILE = ROOT_DIR / "evaluation" / "ground_truth" / "anomaly_labels.json"

PRODUCTS_FILE = RAW_DIR / "products.csv"
USERS_FILE = RAW_DIR / "users.csv"
ORDERS_FILE = RAW_DIR / "orders.csv"

SALES_STATUSES = {"paid", "shipped", "completed"}
TARGET_MONTH = "2025-09"
TARGET_CATEGORY = "Electronics"
SALES_REMAINING_RATIO = Decimal("0.55")

GUANGDONG_TARGET_MONTH = "2026-05"
GUANGDONG_TARGET_REGION = "广东"
GUANGDONG_TARGET_RATIO = Decimal("0.60")
GUANGDONG_RANDOM_SEED = 45

OVERALL_TARGET_MONTH = "2026-07"
OVERALL_REMAINING_RATIO = Decimal("0.55")

OUTLIER_TARGET_MONTH = "2026-08"
OUTLIER_ORDER_COUNT = 15
OUTLIER_MIN_MULTIPLIER = 6
OUTLIER_MAX_MULTIPLIER = 10
OUTLIER_RANDOM_SEED = 46


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    """读取 CSV 文件并返回字段名和记录。"""
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV 缺少表头：{path}")

        return reader.fieldnames, list(reader)


def write_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, str]],
) -> None:
    """将记录写入 UTF-8 CSV 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def inject_electronics_sales_drop(
    orders: list[dict[str, str]],
    products: list[dict[str, str]],
) -> dict:
    """注入 2025 年 9 月电子产品销售额下降 45% 的异常。"""
    product_categories = {
        product["product_id"]: product["category"] for product in products
    }

    affected_orders = []
    baseline_sales = Decimal("0.00")
    actual_sales = Decimal("0.00")

    for order in orders:
        order_month = order["order_time"][:7]

        if (
            order_month != TARGET_MONTH
            or order["order_status"] not in SALES_STATUSES
            or product_categories.get(order["product_id"]) != TARGET_CATEGORY
        ):
            continue

        original_amount = Decimal(order["order_amount"])
        baseline_sales += original_amount

        adjusted_amount = (original_amount * SALES_REMAINING_RATIO).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        order["order_amount"] = f"{adjusted_amount:.2f}"
        actual_sales += adjusted_amount
        affected_orders.append(order["order_id"])

    if not affected_orders or baseline_sales <= 0:
        raise ValueError("没有找到符合条件的电子产品销售订单")

    decrease_ratio = Decimal("1") - actual_sales / baseline_sales

    return {
        "anomaly_id": "A01",
        "anomaly_type": "category_sales_drop",
        "description": "2025 年 9 月电子产品销售额异常下降",
        "target_month": TARGET_MONTH,
        "target_category": TARGET_CATEGORY,
        "sales_statuses": sorted(SALES_STATUSES),
        "target_decrease_ratio": "45%",
        "baseline_sales": f"{baseline_sales:.2f}",
        "actual_sales": f"{actual_sales:.2f}",
        "actual_decrease_ratio": f"{decrease_ratio:.4%}",
        "affected_order_count": len(affected_orders),
        "affected_order_ids": affected_orders,
    }


def inject_guangdong_sales_concentration(
    orders: list[dict[str, str]],
    users: list[dict[str, str]],
) -> dict:
    """注入 2026 年 5 月广东地区销售额占比异常升高的异常。"""
    guangdong_users = [
        user for user in users if user["region"] == GUANGDONG_TARGET_REGION
    ]

    user_regions = {user["user_id"]: user["region"] for user in users}

    total_sales = Decimal("0.00")
    baseline_sales = Decimal("0.00")
    candidates = []

    for order in orders:
        if (
            order["order_time"][:7] != GUANGDONG_TARGET_MONTH
            or order["order_status"] not in SALES_STATUSES
        ):
            continue

        amount = Decimal(order["order_amount"])
        total_sales += amount

        if user_regions[order["user_id"]] == GUANGDONG_TARGET_REGION:
            baseline_sales += amount
            continue

        order_time = datetime.fromisoformat(order["order_time"])

        eligible_users = [
            user
            for user in guangdong_users
            if datetime.fromisoformat(user["register_time"]) <= order_time
        ]

        if not eligible_users:
            continue

        candidates.append(
            {
                "order": order,
                "amount": amount,
                "eligible_users": eligible_users,
            }
        )

    if total_sales <= 0 or not guangdong_users:
        raise ValueError("缺少符合条件的销售额或广东用户")

    target_sales = total_sales * GUANGDONG_TARGET_RATIO
    required_sales = target_sales - baseline_sales

    if required_sales <= 0:
        raise ValueError("广东地区原始销售额已经达到目标，无需注入异常")

    rng = random.Random(GUANGDONG_RANDOM_SEED)
    rng.shuffle(candidates)

    affected_orders = []
    moved_sales = Decimal("0.00")

    for candidate in candidates:
        if baseline_sales + moved_sales >= target_sales:
            break

        selected_user = rng.choice(candidate["eligible_users"])
        candidate["order"]["user_id"] = selected_user["user_id"]

        moved_sales += candidate["amount"]
        affected_orders.append(candidate["order"]["order_id"])

    actual_sales = baseline_sales + moved_sales

    if actual_sales < target_sales:
        raise ValueError("符合条件的订单不足，无法达到广东地区销售额占比目标")

    return {
        "anomaly_id": "A03",
        "anomaly_type": "regional_sales_concentration",
        "description": "2026 年 5 月广东地区销售额占比异常集中",
        "target_month": GUANGDONG_TARGET_MONTH,
        "target_region": GUANGDONG_TARGET_REGION,
        "sales_statuses": sorted(SALES_STATUSES),
        "target_ratio": f"{GUANGDONG_TARGET_RATIO:.0%}",
        "baseline_sales": f"{baseline_sales:.2f}",
        "actual_sales": f"{actual_sales:.2f}",
        "total_sales": f"{total_sales:.2f}",
        "baseline_ratio": f"{baseline_sales / total_sales:.4%}",
        "actual_ratio": f"{actual_sales / total_sales:.4%}",
        "affected_order_count": len(affected_orders),
        "affected_order_ids": affected_orders,
    }


def inject_overall_sales_drop(
    orders: list[dict[str, str]],
) -> dict:
    """注入 2026 年 7 月整体销售额下降 45% 的异常。"""
    affected_orders = []
    baseline_sales = Decimal("0.00")
    actual_sales = Decimal("0.00")

    for order in orders:
        if (
            order["order_time"][:7] != OVERALL_TARGET_MONTH
            or order["order_status"] not in SALES_STATUSES
        ):
            continue

        original_amount = Decimal(order["order_amount"])
        baseline_sales += original_amount

        adjusted_amount = (original_amount * OVERALL_REMAINING_RATIO).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        order["order_amount"] = f"{adjusted_amount:.2f}"
        actual_sales += adjusted_amount
        affected_orders.append(order["order_id"])

    if not affected_orders or baseline_sales <= 0:
        raise ValueError("没有找到符合条件的整体销售订单")

    decrease_ratio = Decimal("1") - actual_sales / baseline_sales

    return {
        "anomaly_id": "A04",
        "anomaly_type": "overall_sales_drop",
        "description": "2026 年 7 月整体销售额异常下降",
        "target_month": OVERALL_TARGET_MONTH,
        "sales_statuses": sorted(SALES_STATUSES),
        "target_decrease_ratio": "45%",
        "baseline_sales": f"{baseline_sales:.2f}",
        "actual_sales": f"{actual_sales:.2f}",
        "actual_decrease_ratio": f"{decrease_ratio:.4%}",
        "affected_order_count": len(affected_orders),
        "affected_order_ids": affected_orders,
    }


def inject_order_amount_outliers(
    orders: list[dict[str, str]],
    products: list[dict[str, str]],
) -> dict:
    """注入 2026 年 8 月 15 笔订单金额异常。"""
    product_prices = {
        product["product_id"]: Decimal(product["price"]) for product in products
    }

    candidates = [
        order
        for order in orders
        if (
            order["order_time"][:7] == OUTLIER_TARGET_MONTH
            and order["order_status"] in SALES_STATUSES
        )
    ]

    if len(candidates) < OUTLIER_ORDER_COUNT:
        raise ValueError(
            f"A05 候选订单不足：需要 {OUTLIER_ORDER_COUNT} 笔，"
            f"实际只有 {len(candidates)} 笔"
        )

    rng = random.Random(OUTLIER_RANDOM_SEED)
    selected_orders = rng.sample(candidates, OUTLIER_ORDER_COUNT)

    affected_orders = []
    baseline_sales = Decimal("0.00")
    actual_sales = Decimal("0.00")

    for order in selected_orders:
        product_id = order["product_id"]
        product_price = product_prices[product_id]
        original_amount = Decimal(order["order_amount"])
        multiplier = rng.randint(
            OUTLIER_MIN_MULTIPLIER,
            OUTLIER_MAX_MULTIPLIER,
        )

        adjusted_amount = (product_price * multiplier).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        order["order_amount"] = f"{adjusted_amount:.2f}"

        baseline_sales += original_amount
        actual_sales += adjusted_amount

        affected_orders.append(
            {
                "order_id": order["order_id"],
                "product_id": product_id,
                "product_price": f"{product_price:.2f}",
                "original_amount": f"{original_amount:.2f}",
                "injected_amount": f"{adjusted_amount:.2f}",
                "multiplier": multiplier,
            }
        )

    return {
        "anomaly_id": "A05",
        "anomaly_type": "order_amount_outliers",
        "description": "2026 年 8 月出现 15 笔订单金额异常偏高",
        "target_month": OUTLIER_TARGET_MONTH,
        "sales_statuses": sorted(SALES_STATUSES),
        "target_multiplier_range": (
            f"{OUTLIER_MIN_MULTIPLIER}-{OUTLIER_MAX_MULTIPLIER}"
        ),
        "baseline_sales": f"{baseline_sales:.2f}",
        "actual_sales": f"{actual_sales:.2f}",
        "affected_order_count": len(affected_orders),
        "affected_order_ids": [item["order_id"] for item in affected_orders],
        "affected_orders": affected_orders,
    }


def main() -> None:
    """读取基础数据、注入异常并导出处理结果。"""
    product_fields, products = read_csv(PRODUCTS_FILE)
    user_fields, users = read_csv(USERS_FILE)
    order_fields, orders = read_csv(ORDERS_FILE)

    anomaly_a01 = inject_electronics_sales_drop(orders, products)
    anomaly_a03 = inject_guangdong_sales_concentration(orders, users)
    anomaly_a04 = inject_overall_sales_drop(orders)
    anomaly_a05 = inject_order_amount_outliers(orders, products)

    anomalies = [
        anomaly_a01,
        anomaly_a03,
        anomaly_a04,
        anomaly_a05,
    ]

    write_csv(PROCESSED_DIR / "products.csv", product_fields, products)
    write_csv(PROCESSED_DIR / "users.csv", user_fields, users)
    write_csv(PROCESSED_DIR / "orders.csv", order_fields, orders)

    LABELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    LABELS_FILE.write_text(
        json.dumps(
            {
                "dataset_version": "1.0",
                "anomalies": anomalies,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print("========== 异常注入完成 ==========")

    for anomaly in anomalies:
        print(f"\n异常编号：{anomaly['anomaly_id']}")
        print(f"目标月份：{anomaly['target_month']}")
        print(f"受影响订单：{anomaly['affected_order_count']}")

        if anomaly["anomaly_id"] == "A01":
            print(f"目标类别：{anomaly['target_category']}")
            print(f"实际下降比例：{anomaly['actual_decrease_ratio']}")
        elif anomaly["anomaly_id"] == "A03":
            print(f"目标地区：{anomaly['target_region']}")
            print(f"原始销售额占比：{anomaly['baseline_ratio']}")
            print(f"注入后销售额占比：{anomaly['actual_ratio']}")
        elif anomaly["anomaly_id"] == "A04":
            print(f"实际下降比例：{anomaly['actual_decrease_ratio']}")
            print(f"注入前销售额：{anomaly['baseline_sales']}")
            print(f"注入后销售额：{anomaly['actual_sales']}")
        elif anomaly["anomaly_id"] == "A05":
            print(f"异常订单金额倍数范围：{anomaly['target_multiplier_range']}")
            print(f"异常订单数量：{anomaly['affected_order_count']}")

    print(f"\n异常数据目录：{PROCESSED_DIR}")
    print(f"标签文件：{LABELS_FILE}")


if __name__ == "__main__":
    main()
