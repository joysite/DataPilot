"""数据集检查相关的数据访问操作。"""

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ImportRecord, Order, Product, User


class DataInspectionRepository:
    """数据集检查数据访问层。"""

    TABLE_MODELS = {
        "users": User,
        "products": Product,
        "orders": Order,
    }

    @staticmethod
    async def get_table_counts(
        session: AsyncSession,
    ) -> dict[str, int]:
        """统计允许检查的业务表记录数量。"""

        counts = {}

        for table_name, model in DataInspectionRepository.TABLE_MODELS.items():
            statement = select(func.count()).select_from(model)
            result = await session.execute(statement)
            counts[table_name] = result.scalar_one()

        return counts

    @staticmethod
    def get_table_schema(
        table_name: str,
    ) -> list[dict[str, str | bool]]:
        """获取指定业务表的字段结构。"""

        model = DataInspectionRepository.TABLE_MODELS.get(table_name)

        if model is None:
            raise ValueError(f"不支持检查的数据表：{table_name}")

        return [
            {
                "field": column.name,
                "type": str(column.type),
                "primary_key": column.primary_key,
                "nullable": column.nullable,
            }
            for column in model.__table__.columns
        ]

    @staticmethod
    async def get_null_counts(
        session: AsyncSession,
        table_name: str,
    ) -> dict[str, int]:
        """统计指定业务表各字段的 NULL 数量。"""
        model = DataInspectionRepository.TABLE_MODELS.get(table_name)

        if model is None:
            raise ValueError(f"不支持检查的数据表：{table_name}")

        columns = model.__table__.columns

        statement = select(
            *[
                func.count(case((column.is_(None), 1))).label(column.name)
                for column in columns
            ]
        )

        result = await session.execute(statement)
        row = result.one()

        return {column.name: row._mapping[column.name] for column in columns}

    @staticmethod
    async def get_integrity_summary(
        session: AsyncSession,
    ) -> dict[str, int]:
        """检查订单关联用户和商品的完整性。"""
        user_statement = (
            select(func.count(Order.order_id))
            .outerjoin(User, Order.user_id == User.user_id)
            .where(User.user_id.is_(None))
        )

        user_result = await session.execute(user_statement)
        orphan_user_orders = user_result.scalar_one()

        product_statement = (
            select(func.count(Order.order_id))
            .outerjoin(Product, Order.product_id == Product.product_id)
            .where(Product.product_id.is_(None))
        )

        product_result = await session.execute(product_statement)
        orphan_product_orders = product_result.scalar_one()

        return {
            "orphan_user_orders": orphan_user_orders,
            "orphan_product_orders": orphan_product_orders,
        }

    @staticmethod
    async def get_import_history(
        session: AsyncSession,
        limit: int = 5,
    ) -> list[dict]:
        """获取最近的数据导入记录。"""
        if not 1 <= limit <= 20:
            raise ValueError("limit 必须在 1 到 20 之间")

        statement = (
            select(ImportRecord)
            .order_by(
                ImportRecord.created_at.desc(),
                ImportRecord.id.desc(),
            )
            .limit(limit)
        )

        result = await session.execute(statement)
        records = result.scalars().all()

        return [
            {
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
            for record in records
        ]
