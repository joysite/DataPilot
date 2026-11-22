"""数据导入记录与错误明细的数据访问层。"""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_error import ImportError
from app.models.import_record import ImportRecord


class ImportRepository:
    """数据导入记录管理操作。"""

    @staticmethod
    async def find_by_hash(
        session: AsyncSession,
        file_hash: str,
        dataset_type: str,
    ) -> ImportRecord | None:
        """查询已有的有效导入记录，失败记录允许重新导入。"""
        result = await session.scalars(
            select(ImportRecord)
            .where(
                ImportRecord.file_hash == file_hash,
                ImportRecord.dataset_type == dataset_type,
                ImportRecord.status.in_(
                    ["processing", "success", "partial", "duplicate"]
                ),
            )
            .order_by(ImportRecord.id.desc())
            .limit(1)
        )
        return result.first()

    @staticmethod
    async def create_record(
        session: AsyncSession,
        file_name: str,
        file_hash: str,
        dataset_type: str,
        total_rows: int = 0,
        status: str = "processing",
    ) -> ImportRecord:
        """创建导入记录，不负责提交事务。"""
        record = ImportRecord(
            file_name=file_name,
            file_hash=file_hash,
            dataset_type=dataset_type,
            total_rows=total_rows,
            imported_rows=0,
            skipped_rows=0,
            failed_rows=0,
            status=status,
            created_at=datetime.now().astimezone(),
        )
        session.add(record)
        await session.flush()
        return record

    @staticmethod
    async def update_record(
        session: AsyncSession,
        record: ImportRecord,
        imported_rows: int,
        skipped_rows: int,
        failed_rows: int,
        status: str,
    ) -> None:
        """更新导入统计和状态，不负责提交事务。"""
        record.imported_rows = imported_rows
        record.skipped_rows = skipped_rows
        record.failed_rows = failed_rows
        record.status = status
        await session.flush()

    @staticmethod
    async def bulk_create_errors(
        session: AsyncSession,
        import_record_id: int,
        errors: list[dict[str, Any]],
    ) -> int:
        """批量保存导入错误明细，不负责提交事务。"""
        if not errors:
            return 0

        error_records = [
            ImportError(
                import_record_id=import_record_id,
                row_number=error["row_number"],
                field_name=error.get("field_name"),
                error_type=error["error_type"],
                error_message=error["error_message"],
                raw_value=error.get("raw_value"),
            )
            for error in errors
        ]

        session.add_all(error_records)
        await session.flush()

        return len(error_records)

    @staticmethod
    async def list_records(
        session: AsyncSession,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ImportRecord]:
        """分页查询导入记录，最新记录优先。"""
        if not 1 <= limit <= 100:
            raise ValueError("limit 必须在 1 到 100 之间")
        if offset < 0:
            raise ValueError("offset 不能小于 0")

        statement = (
            select(ImportRecord)
            .order_by(
                ImportRecord.created_at.desc(),
                ImportRecord.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        result = await session.scalars(statement)
        return list(result.all())

    @staticmethod
    async def count_records(session: AsyncSession) -> int:
        """统计导入记录总数。"""
        statement = select(func.count()).select_from(ImportRecord)
        return await session.scalar(statement) or 0

    @staticmethod
    async def get_record_by_id(
        session: AsyncSession,
        import_record_id: int,
    ) -> ImportRecord | None:
        """根据 ID 查询导入记录。"""
        return await session.get(ImportRecord, import_record_id)

    @staticmethod
    async def get_errors_by_record_id(
        session: AsyncSession,
        import_record_id: int,
    ) -> list[ImportError]:
        """查询指定导入记录的错误明细。"""
        statement = (
            select(ImportError)
            .where(ImportError.import_record_id == import_record_id)
            .order_by(
                ImportError.row_number.asc(),
                ImportError.id.asc(),
            )
        )
        result = await session.scalars(statement)
        return list(result.all())
