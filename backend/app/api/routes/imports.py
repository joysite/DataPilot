"""数据集导入 API。"""

import tempfile
from pathlib import Path, PurePosixPath
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.ingestion.reader import DatasetType
from app.models.import_record import ImportRecord
from app.repositories.import_repository import ImportRepository
from app.services.import_service import import_dataset

router = APIRouter(prefix="/imports", tags=["Imports"])

MAX_UPLOAD_SIZE = 20 * 1024 * 1024
UPLOAD_CHUNK_SIZE = 1024 * 1024


def normalize_filename(filename: str | None) -> str:
    """清理上传文件名，避免路径穿越并保留原始文件名。"""
    if not filename:
        raise HTTPException(status_code=400, detail="上传文件名不能为空。")

    normalized = PurePosixPath(filename.replace("\\", "/")).name

    if normalized in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="上传文件名无效。")

    if Path(normalized).suffix.lower() != ".csv":
        raise HTTPException(status_code=400, detail="仅支持 CSV 文件。")

    return normalized


@router.post(
    "",
    summary="上传并导入 CSV 数据集",
)
async def upload_import(
    dataset_type: Annotated[DatasetType, Form()],
    file: Annotated[UploadFile, File()],
) -> dict:
    """上传 CSV 文件并执行数据导入。"""
    try:
        filename = normalize_filename(file.filename)

        with tempfile.TemporaryDirectory(prefix="datapilot-import-") as temp_dir:
            file_path = Path(temp_dir) / filename
            total_size = 0

            with file_path.open("wb") as destination:
                while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                    total_size += len(chunk)

                    if total_size > MAX_UPLOAD_SIZE:
                        raise HTTPException(
                            status_code=413,
                            detail="上传文件超过 20 MB 限制。",
                        )

                    destination.write(chunk)

            return await import_dataset(file_path, dataset_type)

    finally:
        await file.close()


def serialize_import_record(record: ImportRecord) -> dict:
    """序列化导入记录。"""
    return {
        "id": record.id,
        "file_name": record.file_name,
        "dataset_type": record.dataset_type,
        "total_rows": record.total_rows,
        "imported_rows": record.imported_rows,
        "skipped_rows": record.skipped_rows,
        "failed_rows": record.failed_rows,
        "status": record.status,
        "created_at": record.created_at,
    }


@router.get(
    "",
    summary="分页查询导入历史",
)
async def list_imports(
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    """分页查询数据导入记录。"""
    total = await ImportRepository.count_records(session)
    records = await ImportRepository.list_records(
        session,
        limit=limit,
        offset=offset,
    )

    return {
        "items": [serialize_import_record(record) for record in records],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{import_record_id}",
    summary="查询导入详情及错误明细",
)
async def get_import_detail(
    import_record_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """查询单次导入记录及其错误明细。"""
    record = await ImportRepository.get_record_by_id(
        session,
        import_record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"导入记录不存在：{import_record_id}",
        )

    errors = await ImportRepository.get_errors_by_record_id(
        session,
        import_record_id,
    )

    return {
        **serialize_import_record(record),
        "errors": [
            {
                "id": error.id,
                "row_number": error.row_number,
                "field_name": error.field_name,
                "error_type": error.error_type,
                "error_message": error.error_message,
                "raw_value": error.raw_value,
            }
            for error in errors
        ],
    }
