"""DataPilot 电商模拟数据生成器。"""

import csv
import random
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PRODUCTS_FILE = RAW_DATA_DIR / "products.csv"

RANDOM_SEED = 42
USER_RANDOM_SEED = 43
USER_COUNT = 3000

USERS_FILE = RAW_DATA_DIR / "users.csv"

USER_FIELDS = [
    "user_id",
    "register_time",
    "region",
]

# 地区按业务大区分组，用户数量按大区比例精确分配。
USER_REGION_GROUPS = {
    "first_tier": {
        "count": 1350,
        "regions": [
            "北京",
            "上海",
            "广东",
            "浙江",
            "江苏",
            "四川",
            "湖北",
            "陕西",
            "重庆",
            "天津",
        ],
    },
    "other_eastern": {
        "count": 750,
        "regions": [
            "山东",
            "福建",
            "河北",
            "海南",
        ],
    },
    "central": {
        "count": 540,
        "regions": [
            "河南",
            "湖南",
            "安徽",
            "江西",
            "山西",
        ],
    },
    "western_northeastern": {
        "count": 360,
        "regions": [
            "辽宁",
            "吉林",
            "黑龙江",
            "内蒙古",
            "广西",
            "云南",
            "贵州",
            "西藏",
            "甘肃",
            "青海",
            "宁夏",
            "新疆",
        ],
    },
}

USER_START_TIME = "2024-01-01T00:00:00+08:00"
USER_END_TIME = "2026-10-31T23:59:59+08:00"

ORDER_RANDOM_SEED = 44
USER_WEIGHT_SEED = 45
ORDER_COUNT = 10000
ORDERS_FILE = RAW_DATA_DIR / "orders.csv"

HIGH_ACTIVITY_USER_RATIO = 0.20
HIGH_ACTIVITY_USER_WEIGHT = 4
NORMAL_USER_WEIGHT = 1

PRODUCT_WEIGHT_SEED = 46
HOT_PRODUCT_RATIO = 0.20
HOT_PRODUCT_WEIGHT = 6
NORMAL_PRODUCT_WEIGHT = 1

PROMOTION_MONTHS = {6, 11, 12}
NORMAL_DISCOUNT_RANGE = (90, 100)
PROMOTION_DISCOUNT_RANGE = (75, 90)
MAJOR_PROMOTION_DISCOUNT_RANGE = (60, 80)

ORDER_FIELDS = [
    "order_id",
    "user_id",
    "product_id",
    "order_amount",
    "order_status",
    "order_time",
]

# 每月订单数量，合计严格为 10,000。
MONTHLY_ORDER_COUNTS = {
    "2025-01": 347,
    "2025-02": 289,
    "2025-03": 364,
    "2025-04": 364,
    "2025-05": 374,
    "2025-06": 627,
    "2025-07": 374,
    "2025-08": 382,
    "2025-09": 434,
    "2025-10": 400,
    "2025-11": 771,
    "2025-12": 501,
    "2026-01": 364,
    "2026-02": 289,
    "2026-03": 900,
    "2026-04": 400,
    "2026-05": 443,
    "2026-06": 627,
    "2026-07": 453,
    "2026-08": 463,
    "2026-09": 417,
    "2026-10": 417,
}

ORDER_STATUS_COUNTS = {
    "pending": 800,
    "paid": 1800,
    "shipped": 2000,
    "completed": 4800,
    "cancelled": 600,
}

SALES_STATUSES = {"paid", "shipped", "completed"}

# 类别、商品数量、最低价格（元）、最高价格（元）
PRODUCT_CATEGORIES = {
    "Electronics": (100, 100, 8000),
    "Clothing": (100, 30, 1000),
    "Food": (75, 5, 500),
    "Home": (65, 20, 3000),
    "Beauty": (60, 15, 1500),
    "Sports": (40, 30, 2000),
    "Books": (35, 10, 300),
    "Digital": (25, 5, 2000),
}

PRODUCT_NAME_PREFIXES = {
    "Electronics": "电子产品",
    "Clothing": "服饰商品",
    "Food": "食品商品",
    "Home": "家居商品",
    "Beauty": "美妆商品",
    "Sports": "运动商品",
    "Books": "图书商品",
    "Digital": "数字商品",
}

PRODUCT_FIELDS = [
    "product_id",
    "product_name",
    "category",
    "price",
]


def generate_products(
    seed: int = RANDOM_SEED,
) -> list[dict[str, str]]:
    """生成固定规模的模拟商品数据。"""
    rng = random.Random(seed)
    products = []

    product_id = 1

    for category, (count, min_price, max_price) in PRODUCT_CATEGORIES.items():
        prefix = PRODUCT_NAME_PREFIXES[category]

        for category_index in range(1, count + 1):
            min_cents = min_price * 100
            max_cents = max_price * 100

            price_cents = round(
                rng.triangular(
                    min_cents,
                    max_cents,
                    min_cents,
                )
            )

            products.append(
                {
                    "product_id": f"PRD{product_id:06d}",
                    "product_name": f"{prefix}-{category_index:03d}",
                    "category": category,
                    "price": f"{price_cents / 100:.2f}",
                }
            )

            product_id += 1

    return products


def validate_products(
    products: list[dict[str, str]],
) -> None:
    """验证商品数据的数量、唯一性和价格范围。"""
    expected_count = sum(config[0] for config in PRODUCT_CATEGORIES.values())

    if len(products) != expected_count:
        raise ValueError(f"商品数量错误：预期 {expected_count}，实际 {len(products)}")

    product_ids = [item["product_id"] for item in products]
    product_names = [item["product_name"] for item in products]

    if len(product_ids) != len(set(product_ids)):
        raise ValueError("存在重复商品 ID")

    if len(product_names) != len(set(product_names)):
        raise ValueError("存在重复商品名称")

    for category, (expected_count, min_price, max_price) in PRODUCT_CATEGORIES.items():
        category_products = [item for item in products if item["category"] == category]

        if len(category_products) != expected_count:
            raise ValueError(
                f"{category} 商品数量错误："
                f"预期 {expected_count}，"
                f"实际 {len(category_products)}"
            )

        for product in category_products:
            price = float(product["price"])

            if not min_price <= price <= max_price:
                raise ValueError(f"商品价格超出范围：{product['product_id']}")


def export_products(
    products: list[dict[str, str]],
    output_path: Path = PRODUCTS_FILE,
) -> None:
    """将商品数据导出为 UTF-8 CSV 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=PRODUCT_FIELDS,
        )
        writer.writeheader()
        writer.writerows(products)


def generate_users(
    seed: int = USER_RANDOM_SEED,
) -> list[dict[str, str]]:
    """生成固定规模的模拟用户数据。"""
    from datetime import datetime, timedelta

    rng = random.Random(seed)

    start_time = datetime.fromisoformat(USER_START_TIME)
    end_time = datetime.fromisoformat(USER_END_TIME)

    total_seconds = int((end_time - start_time).total_seconds())

    users = []

    user_id = 1

    for group in USER_REGION_GROUPS.values():
        for _ in range(group["count"]):
            region = rng.choice(group["regions"])

            register_time = start_time + timedelta(
                seconds=rng.randint(0, total_seconds)
            )

            users.append(
                {
                    "user_id": f"USR{user_id:08d}",
                    "register_time": register_time.isoformat(timespec="seconds"),
                    "region": region,
                }
            )

            user_id += 1

    rng.shuffle(users)

    return users


def validate_users(
    users: list[dict[str, str]],
) -> None:
    """验证用户数量、唯一性、地区和注册时间。"""
    from datetime import datetime

    if len(users) != USER_COUNT:
        raise ValueError(f"用户数量错误：预期 {USER_COUNT}，实际 {len(users)}")

    user_ids = [item["user_id"] for item in users]

    if len(user_ids) != len(set(user_ids)):
        raise ValueError("存在重复用户 ID")

    valid_regions = {
        region for group in USER_REGION_GROUPS.values() for region in group["regions"]
    }

    start_time = datetime.fromisoformat(USER_START_TIME)
    end_time = datetime.fromisoformat(USER_END_TIME)

    for user in users:
        if user["region"] not in valid_regions:
            raise ValueError(f"无效用户地区：{user['user_id']}")

        register_time = datetime.fromisoformat(user["register_time"])

        if not start_time <= register_time <= end_time:
            raise ValueError(f"注册时间超出范围：{user['user_id']}")


def export_users(
    users: list[dict[str, str]],
    output_path: Path = USERS_FILE,
) -> None:
    """将用户数据导出为 UTF-8 CSV 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=USER_FIELDS,
        )
        writer.writeheader()
        writer.writerows(users)


def build_product_sampling_weights(
    products: list[dict[str, str]],
    seed: int = PRODUCT_WEIGHT_SEED,
) -> dict[str, int]:
    """为商品建立长尾抽样权重。"""
    rng = random.Random(seed)

    product_ids = [product["product_id"] for product in products]
    hot_product_count = round(len(product_ids) * HOT_PRODUCT_RATIO)

    hot_products = set(rng.sample(product_ids, hot_product_count))

    return {
        product_id: (
            HOT_PRODUCT_WEIGHT if product_id in hot_products else NORMAL_PRODUCT_WEIGHT
        )
        for product_id in product_ids
    }


def select_order_product(
    products: list[dict[str, str]],
    product_weights: dict[str, int],
    rng: random.Random,
) -> dict[str, str]:
    """按照商品长尾权重选择订单商品。"""
    weights = [product_weights[product["product_id"]] for product in products]

    return rng.choices(
        products,
        weights=weights,
        k=1,
    )[0]


def generate_order_amount(
    product_price: str,
    order_time,
    rng: random.Random,
) -> str:
    """根据商品价格、订单月份和随机折扣计算实际订单金额。"""
    month = order_time.month

    if month in PROMOTION_MONTHS:
        discount_range = (
            MAJOR_PROMOTION_DISCOUNT_RANGE
            if rng.random() < 0.5
            else PROMOTION_DISCOUNT_RANGE
        )
    else:
        discount_range = (
            PROMOTION_DISCOUNT_RANGE if rng.random() < 0.2 else NORMAL_DISCOUNT_RANGE
        )

    discount_percent = rng.randint(*discount_range)
    price = Decimal(product_price)
    discount = Decimal(discount_percent) / Decimal("100")

    amount = (price * discount).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    if amount <= 0:
        raise ValueError(f"订单金额必须大于零：{amount}")

    return f"{amount:.2f}"


def generate_order_times(
    seed: int = ORDER_RANDOM_SEED,
) -> list:
    """按照月度配置生成带时区的订单时间。"""
    from datetime import datetime, timedelta

    rng = random.Random(seed)
    order_times = []

    for month, count in MONTHLY_ORDER_COUNTS.items():
        start_time = datetime.fromisoformat(f"{month}-01T00:00:00+08:00")

        if start_time.month == 12:
            next_month = start_time.replace(
                year=start_time.year + 1,
                month=1,
            )
        else:
            next_month = start_time.replace(
                month=start_time.month + 1,
            )

        month_seconds = int((next_month - start_time).total_seconds())

        for _ in range(count):
            offset = rng.randint(0, month_seconds - 1)
            order_times.append(start_time + timedelta(seconds=offset))

    rng.shuffle(order_times)

    return order_times


def build_user_sampling_weights(
    users: list[dict[str, str]],
    seed: int = USER_WEIGHT_SEED,
) -> dict[str, int]:
    """为用户建立长尾抽样权重。"""
    rng = random.Random(seed)

    user_ids = [user["user_id"] for user in users]
    high_activity_count = round(len(user_ids) * HIGH_ACTIVITY_USER_RATIO)

    high_activity_users = set(rng.sample(user_ids, high_activity_count))

    return {
        user_id: (
            HIGH_ACTIVITY_USER_WEIGHT
            if user_id in high_activity_users
            else NORMAL_USER_WEIGHT
        )
        for user_id in user_ids
    }


def select_order_user(
    order_time,
    users: list[dict[str, str]],
    user_weights: dict[str, int],
    rng: random.Random,
) -> dict[str, str]:
    """根据订单时间和长尾权重选择已注册用户。"""
    from datetime import datetime

    eligible_users = [
        user
        for user in users
        if datetime.fromisoformat(user["register_time"]) <= order_time
    ]

    if not eligible_users:
        raise ValueError(f"订单时间 {order_time.isoformat()} 之前没有已注册用户")

    weights = [user_weights[user["user_id"]] for user in eligible_users]

    return rng.choices(
        eligible_users,
        weights=weights,
        k=1,
    )[0]


def generate_orders(
    products: list[dict[str, str]],
    users: list[dict[str, str]],
    seed: int = ORDER_RANDOM_SEED,
) -> list[dict[str, str]]:
    """生成固定规模的模拟订单数据。"""
    rng = random.Random(seed)

    order_times = sorted(generate_order_times(seed))
    product_weights = build_product_sampling_weights(products)
    user_weights = build_user_sampling_weights(users)

    # 预先解析注册时间，避免每次抽样重复解析。
    parsed_users = [
        (
            user,
            datetime.fromisoformat(user["register_time"]),
            user_weights[user["user_id"]],
        )
        for user in users
    ]

    # 精确生成各状态数量，再打乱状态顺序。
    order_statuses = [
        status for status, count in ORDER_STATUS_COUNTS.items() for _ in range(count)
    ]
    rng.shuffle(order_statuses)

    orders = []

    for order_time, order_status in zip(
        order_times,
        order_statuses,
        strict=True,
    ):
        eligible_users = [
            (user, weight)
            for user, register_time, weight in parsed_users
            if register_time <= order_time
        ]

        if not eligible_users:
            raise ValueError(f"订单时间 {order_time.isoformat()} 之前没有已注册用户")

        selected_user = rng.choices(
            [item[0] for item in eligible_users],
            weights=[item[1] for item in eligible_users],
            k=1,
        )[0]

        selected_product = select_order_product(
            products,
            product_weights,
            rng,
        )

        order_amount = generate_order_amount(
            selected_product["price"],
            order_time,
            rng,
        )

        orders.append(
            {
                "order_id": "",
                "user_id": selected_user["user_id"],
                "product_id": selected_product["product_id"],
                "order_amount": order_amount,
                "order_status": order_status,
                "order_time": order_time.isoformat(timespec="seconds"),
            }
        )

    # 按时间排序后统一分配订单 ID。
    for index, order in enumerate(orders, start=1):
        order["order_id"] = f"ORD{index:08d}"

    return orders


def validate_orders(
    orders: list[dict[str, str]],
    products: list[dict[str, str]],
    users: list[dict[str, str]],
) -> None:
    """验证订单数量、唯一性、外键、金额、时间和分布。"""
    from collections import Counter
    from decimal import Decimal

    if len(orders) != ORDER_COUNT:
        raise ValueError(f"订单数量错误：预期 {ORDER_COUNT}，实际 {len(orders)}")

    order_ids = [order["order_id"] for order in orders]

    if len(order_ids) != len(set(order_ids)):
        raise ValueError("存在重复订单 ID")

    product_map = {product["product_id"]: product for product in products}
    user_map = {user["user_id"]: user for user in users}

    monthly_counts = Counter()
    status_counts = Counter()

    for order in orders:
        user = user_map.get(order["user_id"])
        product = product_map.get(order["product_id"])

        if user is None:
            raise ValueError(f"订单引用了不存在的用户：{order['order_id']}")

        if product is None:
            raise ValueError(f"订单引用了不存在的商品：{order['order_id']}")

        order_time = datetime.fromisoformat(order["order_time"])
        register_time = datetime.fromisoformat(user["register_time"])

        if register_time > order_time:
            raise ValueError(f"用户注册时间晚于订单时间：{order['order_id']}")

        amount = Decimal(order["order_amount"])
        price = Decimal(product["price"])

        if amount <= 0 or amount > price:
            raise ValueError(f"订单金额异常：{order['order_id']}")

        if amount.as_tuple().exponent != -2:
            raise ValueError(f"订单金额未保留两位小数：{order['order_id']}")

        monthly_counts[order_time.strftime("%Y-%m")] += 1
        status_counts[order["order_status"]] += 1

    if dict(monthly_counts) != MONTHLY_ORDER_COUNTS:
        raise ValueError("订单月度数量与配置不一致")

    if dict(status_counts) != ORDER_STATUS_COUNTS:
        raise ValueError("订单状态数量与配置不一致")


def export_orders(
    orders: list[dict[str, str]],
    output_path: Path = ORDERS_FILE,
) -> None:
    """将订单数据导出为 UTF-8 CSV 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=ORDER_FIELDS,
        )
        writer.writeheader()
        writer.writerows(orders)


def main() -> None:
    """生成并导出模拟商品、用户和订单数据。"""
    products = generate_products()
    validate_products(products)
    export_products(products)

    users = generate_users()
    validate_users(users)
    export_users(users)

    orders = generate_orders(products, users)
    validate_orders(orders, products, users)
    export_orders(orders)

    print("========== 商品数据生成完成 ==========")
    print(f"商品数量：{len(products)}")
    print(f"商品类别：{len(PRODUCT_CATEGORIES)}")
    print(f"随机种子：{RANDOM_SEED}")
    print(f"输出文件：{PRODUCTS_FILE}")

    print()
    print("========== 用户数据生成完成 ==========")
    print(f"用户数量：{len(users)}")
    print(f"地区大区数量：{len(USER_REGION_GROUPS)}")
    print(f"随机种子：{USER_RANDOM_SEED}")
    print(f"输出文件：{USERS_FILE}")

    print()
    print("========== 订单数据生成完成 ==========")
    print(f"订单数量：{len(orders)}")
    print(f"月份数量：{len(MONTHLY_ORDER_COUNTS)}")
    print(f"随机种子：{ORDER_RANDOM_SEED}")
    print(f"输出文件：{ORDERS_FILE}")


if __name__ == "__main__":
    main()
