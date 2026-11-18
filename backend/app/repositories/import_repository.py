"""数据导入记录与错误明细的数据访问层。"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
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
