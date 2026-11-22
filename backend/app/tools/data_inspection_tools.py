"""数据集检查工具。"""

from datetime import datetime
from typing import Literal

from langchain_core.tools import tool

from app.database.connection import AsyncSessionLocal
from app.services.data_inspection_service import DataInspectionService


def create_data_inspection_tools(session_factory=AsyncSessionLocal):
    """创建绑定指定数据库 Session 工厂的数据检查工具。"""

    @tool
    async def inspect_data(
        table_name: Literal["users", "products", "orders"] | None = None,
    ) -> dict:
        """检查数据库业务数据集的结构和质量。

        可以检查全部业务表，也可以指定 users、products 或 orders。
        返回表记录数量、字段结构、NULL 数量、
        外键完整性和最近的数据导入历史。
        """
        async with session_factory() as session:
            result = await DataInspectionService().inspect_data(
                session=session,
                table_name=table_name,
            )

        for record in result["import_history"]:
            created_at = record["created_at"]
            if isinstance(created_at, datetime):
                record["created_at"] = created_at.isoformat()

        return result

    return {
        "inspect_data": inspect_data,
    }


_DEFAULT_TOOLS = create_data_inspection_tools()

inspect_data = _DEFAULT_TOOLS["inspect_data"]
