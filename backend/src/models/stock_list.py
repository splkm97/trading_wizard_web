"""Stock list model for user-uploaded stock lists."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from src.models.base import Base, generate_uuid


class StockList(Base):
    """User's custom stock list or system default list."""

    __tablename__ = "stock_lists"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    stock_codes = Column(Text, nullable=False)
    stock_count = Column(String(10), nullable=False, default="0")
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="stock_lists")

    def get_stock_codes_list(self) -> list[str]:
        """Return stock codes as a list."""
        return [code.strip() for code in self.stock_codes.strip().split("\n") if code.strip()]

    def __repr__(self):
        return f"<StockList {self.name} ({self.stock_count} stocks)>"
