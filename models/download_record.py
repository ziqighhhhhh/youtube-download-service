from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class DownloadRecord(Base):
    __tablename__ = "download_records"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    video_title = Column(String(500), nullable=True)
    video_id = Column(String(50), nullable=True)
    upload_date = Column(String(20), nullable=True)
    status = Column(String(20), default="pending")
    file_size = Column(Integer, nullable=True)

    task = relationship("Task", back_populates="records")
