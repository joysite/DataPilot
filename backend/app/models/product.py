"""商品 ORM 模型。"""

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Product(Base):
    """电商商品表。"""

    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
