import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import current_user
from ..db import get_session
from ..models import User
from ..schemas import FeedbackIn

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", status_code=204)
async def create(body: FeedbackIn, user: User = Depends(current_user),
                 session: AsyncSession = Depends(get_session)):
    run_id = uuid.UUID(body.run_id) if body.run_id else None
    await session.execute(text("""
        INSERT INTO core.feedback (feedback_id, user_id, run_id, opportunity_id, signal)
        VALUES (:id, :u, :r, :o, :s)
        ON CONFLICT DO NOTHING
    """), {"id": uuid.uuid4(), "u": user.user_id, "r": run_id,
           "o": body.opportunity_id, "s": body.signal})
    await session.commit()