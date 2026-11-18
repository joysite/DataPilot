"""用户 ORM 模型。"""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class User(Base):
    """电商用户表。"""

    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    register_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    region: Mapped[str] = mapped_column(String(20), nullable=False)
