from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database.base import Base
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.ingestion import OrderImport, ProductImport, UserImport
from app.services.import_service import (
    filter_duplicate_primary_keys,
    filter_order_constraints,
)


@pytest.fixture
async def db_session(tmp_path):
    db_path = tmp_path / "ingestion_test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        session.add_all(
            [
                User(
                    user_id="u-existing",
                    register_time=datetime(2025, 1, 1, tzinfo=UTC),
                    region="east",
                ),
                User(
                    user_id="u-valid",
                    register_time=datetime(2025, 1, 2, tzinfo=UTC),
                    region="west",
                ),
                Product(
                    product_id="p-existing",
                    product_name="Existing",
                    category="digital",
                    price=Decimal("10.00"),
                ),
                Product(
                    product_id="p-valid",
                    product_name="Valid",
                    category="daily",
                    price=Decimal("20.00"),
                ),
                Order(
                    order_id="o-existing",
                    user_id="u-existing",
                    product_id="p-existing",
                    order_amount=Decimal("10.00"),
                    order_status="paid",
                    order_time=datetime(2025, 1, 3, tzinfo=UTC),
                ),
            ]
        )
        await session.flush()
        yield session

    await engine.dispose()


def make_user(user_id: str) -> UserImport:
    return UserImport(
        user_id=user_id,
        register_time="2025-02-01T10:00:00+08:00",
        region="east",
    )


def make_product(product_id: str) -> ProductImport:
    return ProductImport(
        product_id=product_id,
        product_name="Test Product",
        category="daily",
        price="12.00",
    )


def make_order(
    order_id: str,
    user_id: str = "u-existing",
    product_id: str = "p-existing",
) -> OrderImport:
    return OrderImport(
        order_id=order_id,
        user_id=user_id,
        product_id=product_id,
        order_amount="30.00",
        order_status="paid",
        order_time="2025-02-01T10:00:00+08:00",
    )


@pytest.mark.asyncio
async def test_user_filter_removes_existing_and_batch_duplicates(db_session):
    rows = [
        make_user("u-existing"),
        make_user("u-new"),
        make_user("u-new"),
        make_user("u-another"),
    ]

    result = await filter_duplicate_primary_keys(
        db_session,
        rows,
        [2, 3, 4, 5],
        "users",
    )

    assert [row.user_id for row in result["valid_rows"]] == [
        "u-new",
        "u-another",
    ]
    assert result["valid_row_numbers"] == [3, 5]
    assert result["skipped_rows"] == 2


@pytest.mark.asyncio
async def test_product_filter_removes_existing_and_batch_duplicates(db_session):
    rows = [
        make_product("p-existing"),
        make_product("p-new"),
        make_product("p-new"),
        make_product("p-another"),
    ]

    result = await filter_duplicate_primary_keys(
        db_session,
        rows,
        [2, 3, 4, 5],
        "products",
    )

    assert [row.product_id for row in result["valid_rows"]] == [
        "p-new",
        "p-another",
    ]
    assert result["valid_row_numbers"] == [3, 5]
    assert result["skipped_rows"] == 2


@pytest.mark.asyncio
async def test_order_filter_removes_existing_and_batch_duplicates(db_session):
    rows = [
        make_order("o-existing"),
        make_order("o-new"),
        make_order("o-new"),
        make_order("o-another"),
    ]

    result = await filter_order_constraints(
        db_session,
        rows,
        [2, 3, 4, 5],
    )

    assert [row.order_id for row in result["valid_rows"]] == [
        "o-new",
        "o-another",
    ]
    assert result["valid_row_numbers"] == [3, 5]
    assert result["skipped_rows"] == 2
    assert result["failed_rows"] == 0
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_order_filter_reports_missing_user(db_session):
    result = await filter_order_constraints(
        db_session,
        [make_order("o-missing-user", user_id="u-unknown")],
        [8],
    )

    assert result["valid_rows"] == []
    assert result["valid_row_numbers"] == []
    assert result["failed_rows"] == 1
    assert result["skipped_rows"] == 0
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row_number"] == 8
    assert result["errors"][0]["field_name"] == "user_id"
    assert result["errors"][0]["error_type"] == "foreign_key_error"
    assert result["errors"][0]["raw_value"] == "u-unknown"


@pytest.mark.asyncio
async def test_order_filter_reports_missing_product(db_session):
    result = await filter_order_constraints(
        db_session,
        [make_order("o-missing-product", product_id="p-unknown")],
        [9],
    )

    assert result["failed_rows"] == 1
    assert len(result["errors"]) == 1
    assert result["errors"][0]["row_number"] == 9
    assert result["errors"][0]["field_name"] == "product_id"
    assert result["errors"][0]["raw_value"] == "p-unknown"


@pytest.mark.asyncio
async def test_order_filter_reports_both_missing_foreign_keys(db_session):
    result = await filter_order_constraints(
        db_session,
        [
            make_order(
                "o-both-missing",
                user_id="u-unknown",
                product_id="p-unknown",
            )
        ],
        [10],
    )

    assert result["valid_rows"] == []
    assert result["failed_rows"] == 1
    assert len(result["errors"]) == 2
    assert {error["field_name"] for error in result["errors"]} == {
        "user_id",
        "product_id",
    }
    assert {error["row_number"] for error in result["errors"]} == {10}


@pytest.mark.asyncio
async def test_order_filter_counts_multiple_failed_rows_once(db_session):
    rows = [
        make_order("o-invalid-1", user_id="u-missing"),
        make_order(
            "o-invalid-2",
            user_id="u-missing",
            product_id="p-missing",
        ),
        make_order("o-valid"),
    ]

    result = await filter_order_constraints(
        db_session,
        rows,
        [11, 12, 13],
    )

    assert len(result["valid_rows"]) == 1
    assert result["valid_row_numbers"] == [13]
    assert result["failed_rows"] == 2
    assert len(result["errors"]) == 3


@pytest.mark.asyncio
async def test_order_filter_handles_empty_batch(db_session):
    result = await filter_order_constraints(db_session, [], [])

    assert result == {
        "valid_rows": [],
        "valid_row_numbers": [],
        "skipped_rows": 0,
        "failed_rows": 0,
        "errors": [],
    }
