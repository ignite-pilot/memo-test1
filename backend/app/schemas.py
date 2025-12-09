"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MemoBase(BaseModel):
    """Base memo schema."""
    title: str = Field(..., min_length=1, max_length=255, description="Memo title")
    content: Optional[str] = Field(None, description="Memo content")


class MemoCreate(MemoBase):
    """Schema for creating a memo."""
    pass


class MemoResponse(MemoBase):
    """Schema for memo response."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = "ok"
    message: str = "Service is healthy"

