"""数据导入业务服务。"""

import hashlib
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import AsyncSessionLocal
from app.ingestion.reader import CSVReadError, DatasetType, read_csv
from app.ingestion.validator import validate_rows
from app.models.import_record import ImportRecord
from app.repositories.import_repository import ImportRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.ingestion import OrderImport

HASH_CHUNK_SIZE = 1024 * 1024


def calculate_file_hash(file_path: str | Path) -> str:
    """计算文件的 SHA256 哈希值。"""
    path = Path(file_path)
    hasher = hashlib.sha256()

    with path.open("rb") as file:
        while chunk := file.read(HASH_CHUNK_SIZE):
            hasher.update(chunk)

    return hasher.hexdigest()


async def create_processing_import_record(
    file_path: str | Path,
    dataset_type: DatasetType,
    file_hash: str | None = None,
    total_rows: int = 0,
) -> ImportRecord:
    """创建并提交 processing 状态的导入记录。"""
    path = Path(file_path)
    file_hash = file_hash or calculate_file_hash(path)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            record = await ImportRepository.create_record(
                session=session,
                file_name=path.name,
                file_hash=file_hash,
                dataset_type=dataset_type,
                total_rows=total_rows,
            )

    return record


async def find_duplicate_import(
    session: AsyncSession,
    file_path: str | Path,
    dataset_type: str,
) -> ImportRecord | None:
    """检查相同数据类型是否已经导入过该文件。"""
    file_hash = calculate_file_hash(file_path)

    return await ImportRepository.find_by_hash(
        session,
        file_hash,
        dataset_type,
    )


async def create_duplicate_import_record(
    file_path: str | Path,
    dataset_type: DatasetType,
    total_rows: int,
    file_hash: str | None = None,
) -> ImportRecord | None:
    """发现重复文件时创建并提交重复导入记录。"""
    path = Path(file_path)
    file_hash = file_hash or calculate_file_hash(path)

    async with AsyncSessionLocal() as session:
        async with session.begin():
            existing_record = await ImportRepository.find_by_hash(
                session,
                file_hash,
                dataset_type,
            )

            if existing_record is None:
                return None

            record = await ImportRepository.create_record(
                session=session,
                file_name=path.name,
                file_hash=file_hash,
                dataset_type=dataset_type,
                total_rows=total_rows,
                status="duplicate",
            )

            await ImportRepository.update_record(
                session=session,
                record=record,
                imported_rows=0,
                skipped_rows=total_rows,
                failed_rows=0,
                status="duplicate",
            )

    return record


def read_import_file(
    file_path: str | Path,
    dataset_type: DatasetType,
) -> list[dict[str, str]]:
    """读取待导入 CSV 文件并验证文件结构。"""
    try:
        return read_csv(file_path, dataset_type)
    except CSVReadError:
        raise


def validate_import_rows(
    rows: list[dict[str, str]],
    dataset_type: DatasetType,
) -> dict[str, Any]:
    """校验 CSV 记录并返回有效数据和错误明细。"""
    return validate_rows(rows, dataset_type)


def build_file_error(error: Exception) -> dict[str, Any]:
    """将文件级异常转换为统一错误明细。"""
    return {
        "row_number": 0,
        "field_name": None,
        "error_type": "csv_file_error",
        "error_message": str(error),
        "raw_value": None,
    }


def build_import_result(
    record: ImportRecord,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """构造统一的导入结果。"""
    return {
        "import_record_id": record.id,
        "file_name": record.file_name,
        "dataset_type": record.dataset_type,
        "total_rows": record.total_rows,
        "imported_rows": record.imported_rows,
        "skipped_rows": record.skipped_rows,
        "failed_rows": record.failed_rows,
        "status": record.status,
        "errors": errors or [],
    }


async def create_failed_import_record(
    file_path: str | Path,
    dataset_type: DatasetType,
    error: Exception,
) -> ImportRecord:
    """文件读取失败时创建导入记录并保存错误明细。"""
    path = Path(file_path)
    file_hash = calculate_file_hash(path) if path.is_file() else ""

    async with AsyncSessionLocal() as session:
        async with session.begin():
            record = await ImportRepository.create_record(
                session=session,
                file_name=path.name,
                file_hash=file_hash,
                dataset_type=dataset_type,
                status="failed",
            )

            await ImportRepository.bulk_create_errors(
                session=session,
                import_record_id=record.id,
                errors=[build_file_error(error)],
            )

            await ImportRepository.update_record(
                session=session,
                record=record,
                imported_rows=0,
                skipped_rows=0,
                failed_rows=0,
                status="failed",
            )

    return record


async def filter_duplicate_primary_keys(
    session: AsyncSession,
    valid_rows: list[BaseModel],
    valid_row_numbers: list[int],
    dataset_type: DatasetType,
) -> dict[str, Any]:
    """过滤数据库中已存在和 CSV 批次内重复的主键。"""
    if dataset_type == "users":
        id_field = "user_id"
        existing_ids = await UserRepository.get_existing_ids(
            session,
            [row.user_id for row in valid_rows],
        )
    elif dataset_type == "products":
        id_field = "product_id"
        existing_ids = await ProductRepository.get_existing_ids(
            session,
            [row.product_id for row in valid_rows],
        )
    else:
        raise ValueError("当前函数只支持 users 和 products 数据集")

    seen_ids = set(existing_ids)
    filtered_rows = []
    filtered_row_numbers = []
    skipped_rows = 0

    for row, row_number in zip(valid_rows, valid_row_numbers, strict=True):
        record_id = getattr(row, id_field)

        if record_id in seen_ids:
            skipped_rows += 1
            continue

        seen_ids.add(record_id)
        filtered_rows.append(row)
        filtered_row_numbers.append(row_number)

    return {
        "valid_rows": filtered_rows,
        "valid_row_numbers": filtered_row_numbers,
        "skipped_rows": skipped_rows,
    }


async def filter_order_constraints(
    session: AsyncSession,
    valid_rows: list[OrderImport],
    valid_row_numbers: list[int],
) -> dict[str, Any]:
    """过滤重复订单，并检查订单用户和商品外键。"""
    if not valid_rows:
        return {
            "valid_rows": [],
            "valid_row_numbers": [],
            "skipped_rows": 0,
            "failed_rows": 0,
            "errors": [],
        }

    # 一、过滤数据库已有订单和批次内重复订单
    existing_order_ids = await OrderRepository.get_existing_ids(
        session,
        [row.order_id for row in valid_rows],
    )

    seen_order_ids = set(existing_order_ids)
    unique_orders = []
    unique_row_numbers = []
    skipped_rows = 0

    for order, row_number in zip(valid_rows, valid_row_numbers, strict=True):
        if order.order_id in seen_order_ids:
            skipped_rows += 1
            continue

        seen_order_ids.add(order.order_id)
        unique_orders.append(order)
        unique_row_numbers.append(row_number)

    # 二、查询订单引用的用户和商品是否存在
    existing_user_ids = await UserRepository.get_existing_ids(
        session,
        list({order.user_id for order in unique_orders}),
    )

    existing_product_ids = await ProductRepository.get_existing_ids(
        session,
        list({order.product_id for order in unique_orders}),
    )

    # 三、检查外键并收集错误
    filtered_orders = []
    filtered_row_numbers = []
    errors = []
    failed_row_numbers = set()

    for order, row_number in zip(
        unique_orders,
        unique_row_numbers,
        strict=True,
    ):
        has_error = False

        if order.user_id not in existing_user_ids:
            errors.append(
                {
                    "row_number": row_number,
                    "field_name": "user_id",
                    "error_type": "foreign_key_error",
                    "error_message": f"用户 ID 不存在：{order.user_id}",
                    "raw_value": order.user_id,
                }
            )
            has_error = True

        if order.product_id not in existing_product_ids:
            errors.append(
                {
                    "row_number": row_number,
                    "field_name": "product_id",
                    "error_type": "foreign_key_error",
                    "error_message": f"商品 ID 不存在：{order.product_id}",
                    "raw_value": order.product_id,
                }
            )
            has_error = True

        if has_error:
            failed_row_numbers.add(row_number)
            continue

        filtered_orders.append(order)
        filtered_row_numbers.append(row_number)

    return {
        "valid_rows": filtered_orders,
        "valid_row_numbers": filtered_row_numbers,
        "skipped_rows": skipped_rows,
        "failed_rows": len(failed_row_numbers),
        "errors": errors,
    }


def determine_import_status(
    imported_rows: int,
    skipped_rows: int,
    failed_rows: int,
) -> str:
    """根据导入统计确定最终状态。"""
    if failed_rows == 0:
        return "success"

    if imported_rows > 0 or skipped_rows > 0:
        return "partial"

    return "failed"


def get_dataset_repository(dataset_type: DatasetType):
    """根据数据集类型获取对应 Repository。"""
    repositories = {
        "users": UserRepository,
        "products": ProductRepository,
        "orders": OrderRepository,
    }

    try:
        return repositories[dataset_type]
    except KeyError:
        raise ValueError(f"不支持的数据集类型：{dataset_type}") from None


async def filter_dataset_rows(
    session: AsyncSession,
    valid_rows: list[BaseModel],
    valid_row_numbers: list[int],
    dataset_type: DatasetType,
) -> dict[str, Any]:
    """根据数据集类型执行对应的业务约束过滤。"""
    if dataset_type == "orders":
        return await filter_order_constraints(
            session,
            valid_rows,
            valid_row_numbers,
        )

    result = await filter_duplicate_primary_keys(
        session,
        valid_rows,
        valid_row_numbers,
        dataset_type,
    )

    result["failed_rows"] = 0
    result["errors"] = []

    return result


async def insert_dataset_rows(
    session: AsyncSession,
    valid_rows: list[BaseModel],
    dataset_type: DatasetType,
) -> int:
    """根据数据集类型批量写入业务数据。"""
    repository = get_dataset_repository(dataset_type)
    return await repository.bulk_insert(session, valid_rows)


async def process_dataset_rows(
    session: AsyncSession,
    rows: list[dict[str, str]],
    dataset_type: DatasetType,
) -> dict[str, Any]:
    """校验、过滤并写入数据集记录。"""
    # 一、Schema 校验
    validation_result = validate_import_rows(rows, dataset_type)

    valid_rows = validation_result["valid_rows"]
    valid_row_numbers = validation_result["valid_row_numbers"]
    errors = validation_result["errors"]

    # Schema 校验失败的记录数，按原始 CSV 行号去重
    failed_row_numbers = {error["row_number"] for error in errors}

    # 二、业务约束过滤
    filter_result = await filter_dataset_rows(
        session,
        valid_rows,
        valid_row_numbers,
        dataset_type,
    )

    filtered_rows = filter_result["valid_rows"]
    skipped_rows = filter_result["skipped_rows"]

    # 三、合并业务约束错误
    errors.extend(filter_result["errors"])

    # 四、写入有效记录
    imported_rows = await insert_dataset_rows(
        session,
        filtered_rows,
        dataset_type,
    )

    return {
        "imported_rows": imported_rows,
        "skipped_rows": skipped_rows,
        "failed_rows": len(failed_row_numbers) + filter_result["failed_rows"],
        "errors": errors,
    }


async def import_dataset(
    file_path: str | Path,
    dataset_type: DatasetType,
) -> dict[str, Any]:
    """执行完整的数据集导入流程。"""
    path = Path(file_path)

    # 一、读取 CSV 文件
    try:
        rows = read_import_file(path, dataset_type)
    except (CSVReadError, OSError) as error:
        record = await create_failed_import_record(
            path,
            dataset_type,
            error,
        )
        return build_import_result(
            record,
            [build_file_error(error)],
        )

    total_rows = len(rows)

    # 二、计算文件哈希
    file_hash = calculate_file_hash(path)

    # 三、检查重复文件
    duplicate_record = await create_duplicate_import_record(
        file_path=path,
        dataset_type=dataset_type,
        total_rows=total_rows,
        file_hash=file_hash,
    )

    if duplicate_record is not None:
        return build_import_result(duplicate_record)

    # 四、事务 A：创建 processing 导入记录
    record = await create_processing_import_record(
        file_path=path,
        dataset_type=dataset_type,
        file_hash=file_hash,
        total_rows=total_rows,
    )

    # 五、事务 B：校验、过滤并写入业务数据
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                process_result = await process_dataset_rows(
                    session,
                    rows,
                    dataset_type,
                )

        imported_rows = process_result["imported_rows"]
        skipped_rows = process_result["skipped_rows"]
        failed_rows = process_result["failed_rows"]
        errors = process_result["errors"]

        status = determine_import_status(
            imported_rows,
            skipped_rows,
            failed_rows,
        )

    except Exception as error:
        # 事务 B 已经回滚，业务数据不会残留
        imported_rows = 0
        skipped_rows = 0
        failed_rows = total_rows

        errors = [
            {
                "row_number": 0,
                "field_name": None,
                "error_type": "import_processing_error",
                "error_message": str(error),
                "raw_value": None,
            }
        ]

        status = "failed"

    # 六、事务 C：独立保存错误明细和最终导入状态
    async with AsyncSessionLocal() as session:
        async with session.begin():
            current_record = await session.get(
                ImportRecord,
                record.id,
            )

            if current_record is None:
                raise RuntimeError(f"导入记录不存在：{record.id}")

            await ImportRepository.bulk_create_errors(
                session=session,
                import_record_id=current_record.id,
                errors=errors,
            )

            await ImportRepository.update_record(
                session=session,
                record=current_record,
                imported_rows=imported_rows,
                skipped_rows=skipped_rows,
                failed_rows=failed_rows,
                status=status,
            )

    return build_import_result(
        current_record,
        errors,
    )
