"""Database models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class Memo(Base):
    """Memo model."""
    __tablename__ = "memos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

