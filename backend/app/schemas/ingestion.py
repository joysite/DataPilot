"""数据导入专用 Pydantic Schema。"""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class ImportSchema(BaseModel):
    """导入数据的基础 Schema。"""

    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def strip_string(cls, value):
        """清理字符串首尾空格，并拒绝空字符串。"""
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("字段不能为空")
        return value


class UserImport(ImportSchema):
    """用户导入数据。"""

    user_id: str
    register_time: datetime
    region: str

    @field_validator("register_time")
    @classmethod
    def validate_register_time(cls, value: datetime) -> datetime:
        """要求注册时间包含时区。"""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("注册时间必须包含时区")
        return value


class ProductImport(ImportSchema):
    """商品导入数据。"""

    product_id: str
    product_name: str
    category: str
    price: Decimal

    @field_validator("price")
    @classmethod
    def validate_price(cls, value: Decimal) -> Decimal:
        """校验商品价格。"""
        if value <= 0:
            raise ValueError("商品价格必须大于 0")
        if value.as_tuple().exponent != -2:
            raise ValueError("商品价格必须保留两位小数")
        return value


class OrderImport(ImportSchema):
    """订单导入数据。"""

    order_id: str
    user_id: str
    product_id: str
    order_amount: Decimal
    order_status: Literal[
        "pending",
        "paid",
        "shipped",
        "completed",
        "cancelled",
    ]
    order_time: datetime

    @field_validator("order_amount")
    @classmethod
    def validate_order_amount(cls, value: Decimal) -> Decimal:
        """校验订单金额。"""
        if value <= 0:
            raise ValueError("订单金额必须大于 0")
        if value.as_tuple().exponent != -2:
            raise ValueError("订单金额必须保留两位小数")
        return value

    @field_validator("order_time")
    @classmethod
    def validate_order_time(cls, value: datetime) -> datetime:
        """要求订单时间包含时区。"""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("订单时间必须包含时区")
        return value
