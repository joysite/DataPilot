"""数据质量检查 API。"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.data_inspection_service import DataInspectionService

router = APIRouter(prefix="/data-inspection", tags=["Data Inspection"])

DatasetTable = Literal["users", "products", "orders"]


@router.get(
    "",
    summary="获取数据质量概览",
)
async def inspect_data(
    session: Annotated[AsyncSession, Depends(get_db)],
    table_name: Annotated[DatasetTable | None, Query()] = None,
) -> dict:
    """获取数据表数量、结构、空值、关联完整性和导入历史。"""
    service = DataInspectionService()
    return await service.inspect_data(
        session,
        table_name=table_name,
    )
