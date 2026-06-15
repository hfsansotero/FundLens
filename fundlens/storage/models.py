from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Boolean, Date, DateTime, ForeignKey, Identity, Integer,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fundlens.storage.database import Base


class Fund(Base):
    __tablename__ = "funds"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    manager: Mapped[Optional[str]] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prices: Mapped[list["Price"]] = relationship(back_populates="fund")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="fund")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="fund")
    ingestion_logs: Mapped[list["IngestionLog"]] = relationship(back_populates="fund")


class Price(Base):
    __tablename__ = "prices"
    __table_args__ = (UniqueConstraint("fund_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    nav: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    log_return: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    source: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    fund: Mapped["Fund"] = relationship(back_populates="prices")


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (UniqueConstraint("fund_id", "date"),)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    rolling_vol_30: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    rolling_vol_90: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    sharpe_90: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))

    fund: Mapped["Fund"] = relationship(back_populates="metrics")


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    predicted_for: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_at: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_value: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    lower_bound: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    upper_bound: Mapped[Optional[float]] = mapped_column(Numeric(12, 4))
    model_params: Mapped[Optional[str]] = mapped_column(Text)  # JSON string

    fund: Mapped["Fund"] = relationship(back_populates="predictions")


class ModelScore(Base):
    __tablename__ = "model_scores"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    fund_id: Mapped[int] = mapped_column(ForeignKey("funds.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    eval_date: Mapped[date] = mapped_column(Date, nullable=False)
    mae: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    rmse: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    mape: Mapped[Optional[float]] = mapped_column(Numeric(10, 6))
    horizon_days: Mapped[Optional[int]] = mapped_column(Integer)


class IngestionLog(Base):
    __tablename__ = "ingestion_log"

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True)
    fund_id: Mapped[Optional[int]] = mapped_column(ForeignKey("funds.id"))
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success | failed | missing_from_source
    source: Mapped[Optional[str]] = mapped_column(String(50))
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    fund: Mapped[Optional["Fund"]] = relationship(back_populates="ingestion_logs")
