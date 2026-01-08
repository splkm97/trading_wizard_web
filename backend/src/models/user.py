"""User model for PEM key-based authentication."""

from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from src.models.base import BaseModel


class User(BaseModel):
    """User model with ECDSA P-256 public key authentication."""

    __tablename__ = "users"

    # ECDSA P-256 public key in PEM format
    public_key = Column(String, nullable=False, unique=True)

    # SHA-256 fingerprint of public key (64 hex chars) - used as user identifier
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)

    # Optional display nickname
    nickname = Column(String(50), nullable=True)

    # Timestamps
    last_login_at = Column(DateTime, nullable=True)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    backtest_results = relationship("BacktestResult", back_populates="user")
    stock_lists = relationship("StockList", back_populates="user")

    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()

    def __repr__(self):
        return f"<User(fingerprint={self.fingerprint[:16]}..., nickname={self.nickname})>"
