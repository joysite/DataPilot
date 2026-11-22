from pathlib import Path

import pytest

from app.ingestion.reader import CSVReadError, read_csv
from app.ingestion.validator import validate_rows


def write_csv(tmp_path: Path, content: str, filename: str = "data.csv") -> Path:
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    return path


# ---------- CSV Reader ----------


def test_reader_reads_valid_users_csv(tmp_path):
    path = write_csv(
        tmp_path,
        "user_id,register_time,region\nU001,2025-01-01T10:00:00+08:00,Shanghai\n",
    )

    assert read_csv(path, "users") == [
        {
            "user_id": "U001",
            "register_time": "2025-01-01T10:00:00+08:00",
            "region": "Shanghai",
        }
    ]


def test_reader_supports_utf8_bom(tmp_path):
    path = tmp_path / "bom.csv"
    path.write_bytes(
        "\ufeffuser_id,register_time,region\n"
        "U001,2025-01-01T10:00:00+08:00,Shanghai\n".encode("utf-8")
    )

    assert read_csv(path, "users")[0]["user_id"] == "U001"


def test_reader_returns_empty_list_for_header_only_csv(tmp_path):
    path = write_csv(tmp_path, "user_id,register_time,region\n")

    assert read_csv(path, "users") == []


def test_reader_rejects_missing_file(tmp_path):
    with pytest.raises(CSVReadError, match="不存在"):
        read_csv(tmp_path / "missing.csv", "users")


def test_reader_rejects_empty_file(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")

    with pytest.raises(CSVReadError, match="为空"):
        read_csv(path, "users")


def test_reader_rejects_duplicate_headers(tmp_path):
    path = write_csv(
        tmp_path,
        "user_id,register_time,region,user_id\n",
    )

    with pytest.raises(CSVReadError, match="重复列名"):
        read_csv(path, "users")


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            "user_id,register_time\nU001,2025-01-01T10:00:00+08:00\n",
            "缺少必需字段",
        ),
        (
            "user_id,register_time,region,extra\n"
            "U001,2025-01-01T10:00:00+08:00,Shanghai,x\n",
            "未知字段",
        ),
        (
            "user_id,register_time,region\nU001,2025-01-01T10:00:00+08:00\n",
            "字段数量不足",
        ),
        (
            "user_id,register_time,region\n"
            "U001,2025-01-01T10:00:00+08:00,Shanghai,extra\n",
            "字段数量超过",
        ),
    ],
)
def test_reader_rejects_invalid_csv_structure(tmp_path, content, message):
    path = write_csv(tmp_path, content)

    with pytest.raises(CSVReadError, match=message):
        read_csv(path, "users")


def test_reader_rejects_invalid_encoding(tmp_path):
    path = tmp_path / "invalid.csv"
    path.write_bytes(b"user_id,register_time,region\n\xff,\xfe,x\n")

    with pytest.raises(CSVReadError, match="编码错误"):
        read_csv(path, "users")


# ---------- Row Validator ----------


@pytest.mark.parametrize(
    ("dataset_type", "row", "expected_type"),
    [
        (
            "users",
            {
                "user_id": "U001",
                "register_time": "2025-01-01T10:00:00+08:00",
                "region": "Shanghai",
            },
            "users",
        ),
        (
            "products",
            {
                "product_id": "P001",
                "product_name": "Keyboard",
                "category": "Electronics",
                "price": "199.00",
            },
            "products",
        ),
        (
            "orders",
            {
                "order_id": "O001",
                "user_id": "U001",
                "product_id": "P001",
                "order_amount": "199.00",
                "order_status": "paid",
                "order_time": "2025-01-01T10:00:00+08:00",
            },
            "orders",
        ),
    ],
)
def test_validator_accepts_valid_rows(dataset_type, row, expected_type):
    result = validate_rows([row], dataset_type)

    assert len(result["valid_rows"]) == 1
    assert result["valid_row_numbers"] == [2]
    assert result["errors"] == []
    assert (
        result["valid_rows"][0]
        .__class__.__name__.lower()
        .startswith(expected_type[:-1])
    )


def test_validator_strips_string_values():
    result = validate_rows(
        [
            {
                "user_id": " U001 ",
                "register_time": "2025-01-01T10:00:00+08:00",
                "region": " Shanghai ",
            }
        ],
        "users",
    )

    assert result["valid_rows"][0].user_id == "U001"
    assert result["valid_rows"][0].region == "Shanghai"


@pytest.mark.parametrize(
    ("dataset_type", "row", "field_name", "error_type"),
    [
        (
            "users",
            {
                "user_id": "U001",
                "register_time": "2025-01-01T10:00:00",
                "region": "Shanghai",
            },
            "register_time",
            "invalid_value",
        ),
        (
            "products",
            {
                "product_id": "P001",
                "product_name": "Keyboard",
                "category": "Electronics",
                "price": "invalid",
            },
            "price",
            "decimal_error",
        ),
        (
            "products",
            {
                "product_id": "P001",
                "product_name": "Keyboard",
                "category": "Electronics",
                "price": "0.00",
            },
            "price",
            "invalid_value",
        ),
        (
            "products",
            {
                "product_id": "P001",
                "product_name": "Keyboard",
                "category": "Electronics",
                "price": "10.5",
            },
            "price",
            "invalid_value",
        ),
        (
            "orders",
            {
                "order_id": "O001",
                "user_id": "U001",
                "product_id": "P001",
                "order_amount": "199.00",
                "order_status": "unknown",
                "order_time": "2025-01-01T10:00:00+08:00",
            },
            "order_status",
            "invalid_enum",
        ),
    ],
)
def test_validator_reports_invalid_field(dataset_type, row, field_name, error_type):
    result = validate_rows([row], dataset_type)

    assert result["valid_rows"] == []
    assert len(result["errors"]) >= 1
    assert any(
        error["field_name"] == field_name and error["error_type"] == error_type
        for error in result["errors"]
    )


def test_validator_collects_multiple_errors_and_preserves_row_numbers():
    rows = [
        {
            "user_id": "U001",
            "register_time": "2025-01-01T10:00:00+08:00",
            "region": "Shanghai",
        },
        {
            "user_id": "",
            "register_time": "invalid",
            "region": "Beijing",
        },
        {
            "user_id": "U003",
            "register_time": "2025-01-03T10:00:00+08:00",
            "region": "Shenzhen",
        },
    ]

    result = validate_rows(rows, "users")

    assert result["valid_row_numbers"] == [2, 4]
    assert len(result["errors"]) >= 2
    assert {error["row_number"] for error in result["errors"]} == {3}


def test_validator_supports_custom_start_row_number():
    result = validate_rows(
        [
            {
                "user_id": "U001",
                "register_time": "2025-01-01T10:00:00+08:00",
                "region": "Shanghai",
            }
        ],
        "users",
        start_row_number=10,
    )

    assert result["valid_row_numbers"] == [10]
