"""Memo router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Memo
from app.schemas import MemoCreate, MemoResponse

router = APIRouter(prefix="/api", tags=["memos"])


@router.get("/memos", response_model=List[MemoResponse])
async def get_memos(db: Session = Depends(get_db)):
    """Get all memos."""
    memos = db.query(Memo).order_by(Memo.created_at.desc()).all()
    return memos


@router.post("/memos", response_model=MemoResponse, status_code=status.HTTP_201_CREATED)
async def create_memo(memo: MemoCreate, db: Session = Depends(get_db)):
    """Create a new memo."""
    db_memo = Memo(title=memo.title, content=memo.content)
    db.add(db_memo)
    db.commit()
    db.refresh(db_memo)
    return db_memo


@router.delete("/memos/{memo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memo(memo_id: int, db: Session = Depends(get_db)):
    """Delete a memo."""
    db_memo = db.query(Memo).filter(Memo.id == memo_id).first()
    if not db_memo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Memo with id {memo_id} not found"
        )
    db.delete(db_memo)
    db.commit()
    return None

