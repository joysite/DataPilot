"""业务分析 API。"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def validate_date_range(
    start_date: date | None,
    end_date: date | None,
) -> None:
    """校验日期范围。"""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="开始日期不能晚于结束日期。",
        )


@router.get(
    "/summary",
    summary="获取订单核心指标",
)
async def get_order_summary(
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> dict:
    """获取 GMV、有效订单量、客单价及订单状态统计。"""
    validate_date_range(start_date, end_date)

    service = AnalyticsService()
    return await service.get_order_summary(
        session,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/trend",
    summary="获取月度 GMV 趋势",
)
async def get_gmv_trend(
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[dict]:
    """获取指定日期范围内的月度 GMV 趋势。"""
    validate_date_range(start_date, end_date)

    service = AnalyticsService()
    return await service.analyze_trend(
        session,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/categories",
    summary="获取品类业务对比",
)
async def compare_categories(
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[date | None, Query()] = None,
    end_date: Annotated[date | None, Query()] = None,
) -> list[dict]:
    """获取各品类 GMV、有效订单量和客单价。"""
    validate_date_range(start_date, end_date)

    service = AnalyticsService()
    return await service.compare_categories(
        session,
        start_date=start_date,
        end_date=end_date,
    )
