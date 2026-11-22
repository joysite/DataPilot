"""数据集检查服务。"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.data_inspection_repository import (
    DataInspectionRepository,
)


class DataInspectionService:
    """数据集检查服务。"""

    async def inspect_data(
        self,
        session: AsyncSession,
        table_name: str | None = None,
    ) -> dict:
        """检查数据集结构、质量和导入情况。"""

        if (
            table_name is not None
            and table_name not in DataInspectionRepository.TABLE_MODELS
        ):
            raise ValueError(f"不支持检查的数据表：{table_name}")

        table_counts = await DataInspectionRepository.get_table_counts(session)
        target_tables = (
            [table_name]
            if table_name is not None
            else list(DataInspectionRepository.TABLE_MODELS)
        )

        table_details = {}

        for name in target_tables:
            table_details[name] = {
                "schema": DataInspectionRepository.get_table_schema(name),
                "null_counts": await DataInspectionRepository.get_null_counts(
                    session,
                    name,
                ),
            }

        integrity = await DataInspectionRepository.get_integrity_summary(session)

        import_history = await DataInspectionRepository.get_import_history(
            session,
            limit=5,
        )

        return {
            "table_counts": table_counts,
            "table_details": table_details,
            "integrity": integrity,
            "import_history": import_history,
        }
