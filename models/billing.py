from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import UTC, datetime


def utc_now():
    return datetime.now(UTC)


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    user = relationship("User")
