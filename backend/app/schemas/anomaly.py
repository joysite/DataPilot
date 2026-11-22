"""异常检测结果 Schema。"""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

AnomalyType = Literal[
    "category_gmv_drop",
    "order_count_spike",
    "region_gmv_concentration",
    "overall_gmv_drop",
    "abnormal_order_amount",
]


class AnomalyResult(BaseModel):
    """统一异常检测结果。"""

    model_config = ConfigDict(extra="forbid")

    anomaly_type: AnomalyType = Field(description="异常类型")
    target_month: str = Field(
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="异常目标月份",
    )


class CategoryGMVDropAnomaly(AnomalyResult):
    """品类 GMV 异常下降。"""

    anomaly_type: Literal["category_gmv_drop"]
    category: str = Field(description="商品品类")
    actual_gmv: Decimal = Field(description="实际 GMV")
    baseline_gmv: Decimal = Field(description="历史基线 GMV")
    drop_rate: Decimal = Field(description="GMV 下降比例")
    threshold: Decimal = Field(description="异常判断阈值")


class OrderCountSpikeAnomaly(AnomalyResult):
    """月度订单量异常突增。"""

    anomaly_type: Literal["order_count_spike"]
    actual_count: int = Field(description="实际订单量")
    baseline_count: int = Field(description="去年同期订单量")
    growth_rate: Decimal = Field(description="订单量同比增长率")
    threshold: Decimal = Field(description="异常判断阈值")


class RegionGMVConcentrationAnomaly(AnomalyResult):
    """地区 GMV 占比异常集中。"""

    anomaly_type: Literal["region_gmv_concentration"]
    region: str = Field(description="异常集中地区")
    actual_share: Decimal = Field(description="当前地区 GMV 占比")
    baseline_share: Decimal = Field(description="历史平均 GMV 占比")
    share_increase: Decimal = Field(description="占比增加幅度")
    threshold: Decimal = Field(description="地区占比阈值")
    increase_threshold: Decimal = Field(description="占比增加阈值")


class OverallGMVDropAnomaly(AnomalyResult):
    """整体 GMV 异常下降。"""

    anomaly_type: Literal["overall_gmv_drop"]
    actual_gmv: Decimal = Field(description="实际 GMV")
    baseline_gmv: Decimal = Field(description="历史基线 GMV")
    drop_rate: Decimal = Field(description="GMV 下降比例")
    threshold: Decimal = Field(description="异常判断阈值")


class AbnormalOrderAmountAnomaly(AnomalyResult):
    """订单金额相对商品标价异常。"""

    anomaly_type: Literal["abnormal_order_amount"]
    order_id: str = Field(description="订单 ID")
    product_id: str = Field(description="商品 ID")
    order_amount: Decimal = Field(description="订单金额")
    product_price: Decimal = Field(description="商品标价")
    amount_ratio: Decimal = Field(description="订单金额与商品标价的倍数")
    threshold: Decimal = Field(description="异常判断阈值")


AnomalyResultUnion = Annotated[
    (
        CategoryGMVDropAnomaly
        | OrderCountSpikeAnomaly
        | RegionGMVConcentrationAnomaly
        | OverallGMVDropAnomaly
        | AbnormalOrderAmountAnomaly
    ),
    Field(discriminator="anomaly_type"),
]
