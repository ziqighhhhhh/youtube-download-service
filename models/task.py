from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    youtube_url = Column(String(1000), nullable=False)
    status = Column(String(50), default="pending")
    video_count_total = Column(Integer, default=0)
    video_count_success = Column(Integer, default=0)
    video_count_failed = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User")
    records = relationship("DownloadRecord", back_populates="task")
