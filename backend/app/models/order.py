"""订单 ORM 模型。"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Order(Base):
    """电商订单表。"""

    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[str] = mapped_column(
        String(20),
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    order_status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    order_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
