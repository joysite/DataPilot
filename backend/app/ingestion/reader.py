"""CSV 文件读取与结构验证。"""

import csv
from pathlib import Path
from typing import Literal

DatasetType = Literal["users", "products", "orders"]

REQUIRED_COLUMNS: dict[DatasetType, tuple[str, ...]] = {
    "users": ("user_id", "register_time", "region"),
    "products": ("product_id", "product_name", "category", "price"),
    "orders": (
        "order_id",
        "user_id",
        "product_id",
        "order_amount",
        "order_status",
        "order_time",
    ),
}


class CSVReadError(Exception):
    """CSV 文件读取异常。"""


def read_csv(
    file_path: str | Path,
    dataset_type: DatasetType,
) -> list[dict[str, str]]:
    """读取 CSV 文件并验证表头和记录结构。"""
    path = Path(file_path)

    if not path.is_file():
        raise CSVReadError(f"CSV 文件不存在：{path}")

    if path.stat().st_size == 0:
        raise CSVReadError(f"CSV 文件为空：{path}")

    required_columns = REQUIRED_COLUMNS[dataset_type]

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)

            headers = next(reader, None)

            if headers is None:
                raise CSVReadError("CSV 文件缺少表头")

            if len(headers) != len(set(headers)):
                raise CSVReadError("CSV 文件存在重复列名")

            missing = set(required_columns) - set(headers)
            extra = set(headers) - set(required_columns)

            if missing:
                raise CSVReadError(f"CSV 缺少必需字段：{sorted(missing)}")

            if extra:
                raise CSVReadError(f"CSV 存在未知字段：{sorted(extra)}")

            rows: list[dict[str, str]] = []

            for row_number, values in enumerate(reader, start=2):
                if len(values) > len(headers):
                    raise CSVReadError(f"第 {row_number} 行字段数量超过表头")

                if len(values) < len(headers):
                    raise CSVReadError(f"第 {row_number} 行字段数量不足表头")

                rows.append(dict(zip(headers, values, strict=True)))

            return rows

    except UnicodeDecodeError as exc:
        raise CSVReadError("CSV 文件编码错误，仅支持 UTF-8 和 UTF-8 BOM") from exc
    except csv.Error as exc:
        raise CSVReadError(f"CSV 文件格式错误：{exc}") from exc
