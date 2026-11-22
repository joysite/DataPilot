"""异常检测 API。"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.anomaly import AnomalyResultUnion
from app.services.anomaly_service import AnomalyService

router = APIRouter(prefix="/anomalies", tags=["Anomalies"])


@router.get(
    "",
    summary="执行业务异常检测",
    response_model=list[AnomalyResultUnion],
)
async def detect_anomalies(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[AnomalyResultUnion]:
    """检测品类 GMV 下降、订单量突增、地区 GMV 集中等业务异常。"""

    service = AnomalyService()
    return await service.detect_anomalies(session)
