"""CSV 记录内容校验与类型转换。"""

from typing import Any

from pydantic import BaseModel, ValidationError

from app.ingestion.reader import DatasetType
from app.schemas.ingestion import OrderImport, ProductImport, UserImport

SCHEMA_MAP: dict[DatasetType, type[BaseModel]] = {
    "users": UserImport,
    "products": ProductImport,
    "orders": OrderImport,
}


def _get_error_type(error_type: str) -> str:
    """将 Pydantic 错误类型映射为业务错误类型。"""
    if error_type == "missing":
        return "missing_field"
    if error_type == "extra_forbidden":
        return "unknown_field"
    if error_type.startswith("decimal"):
        return "decimal_error"
    if error_type.startswith("datetime"):
        return "datetime_error"
    if error_type == "literal_error":
        return "invalid_enum"
    if error_type in {"value_error", "string_type"}:
        return "invalid_value"
    return "validation_error"


def validate_rows(
    rows: list[dict[str, str]],
    dataset_type: DatasetType,
    start_row_number: int = 2,
) -> dict[str, list[Any]]:
    """逐行校验记录，收集全部字段错误。"""
    schema = SCHEMA_MAP[dataset_type]

    valid_rows: list[BaseModel] = []
    valid_row_numbers: list[int] = []
    errors: list[dict[str, Any]] = []

    for row_number, row in enumerate(rows, start=start_row_number):
        try:
            record = schema.model_validate(row)
        except ValidationError as exc:
            for error in exc.errors():
                location = error["loc"]
                field_name = str(location[0]) if location else None

                raw_value = row.get(field_name) if field_name else None

                errors.append(
                    {
                        "row_number": row_number,
                        "field_name": field_name,
                        "error_type": _get_error_type(error["type"]),
                        "error_message": error["msg"],
                        "raw_value": raw_value,
                    }
                )
        else:
            valid_rows.append(record)
            valid_row_numbers.append(row_number)

    return {
        "valid_rows": valid_rows,
        "valid_row_numbers": valid_row_numbers,
        "errors": errors,
    }
