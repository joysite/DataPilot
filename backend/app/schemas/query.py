"""受限业务明细查询 Schema。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class QueryDatabaseRequest(BaseModel):
    """受限业务明细查询参数。"""

    model_config = ConfigDict(extra="forbid")

    entity: Literal["orders", "products", "users"] = Field(description="查询实体")
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="最大返回数量",
    )
    order_status: (
        Literal[
            "pending",
            "paid",
            "shipped",
            "completed",
            "cancelled",
        ]
        | None
    ) = Field(
        default=None,
        description="订单状态，仅适用于订单查询",
    )
    user_id: str | None = Field(
        default=None,
        description="用户 ID，仅适用于订单查询",
    )
    product_id: str | None = Field(
        default=None,
        description="商品 ID，仅适用于订单查询",
    )
