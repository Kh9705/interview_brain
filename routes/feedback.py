from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from database import get_db
from models import FeedbackCreateRequest, FeedbackOut

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
async def create_feedback(body: FeedbackCreateRequest, user: dict = Depends(get_current_user)):
    """Record interview feedback and remember it in the knowledge graph."""
    try:
        user_id = user["id"]
        feedback_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # 1. Save to SQLite
        db = await get_db()
        await db.execute(
            """INSERT INTO feedback (id, user_id, company, topic, result, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (feedback_id, user_id, body.company, body.topic, body.result, body.notes, now),
        )
        await db.commit()

        # 2. Remember feedback in Cognee for future recall
        feedback_text = (
            f"Interview Feedback Entry\n"
            f"Company: {body.company}\n"
            f"Topic: {body.topic}\n"
            f"Result: {body.result}\n"
            f"Notes: {body.notes}\n"
            f"Date: {now}\n\n"
            f"The candidate received a '{body.result}' result on the topic '{body.topic}' "
            f"during preparation for {body.company}. "
            f"{'This is an area that needs improvement.' if body.result.lower() in ('fail', 'weak', 'poor', 'needs improvement') else 'The candidate performed well in this area.'}"
        )
        profile_dataset = f"{user_id}_profile"
        await cognee_client.remember(profile_dataset, feedback_text)

        return FeedbackOut(
            id=feedback_id,
            user_id=user_id,
            company=body.company,
            topic=body.topic,
            result=body.result,
            notes=body.notes,
            created_at=now,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/feedback", response_model=list[FeedbackOut])
async def list_feedback(user: dict = Depends(get_current_user)):
    """Return all feedback entries for the current user."""
    try:
        db = await get_db()
        cursor = await db.execute(
            "SELECT * FROM feedback WHERE user_id = ? ORDER BY created_at DESC",
            (user["id"],),
        )
        rows = await cursor.fetchall()
        return [
            FeedbackOut(
                id=row["id"],
                user_id=row["user_id"],
                company=row["company"],
                topic=row["topic"],
                result=row["result"],
                notes=row["notes"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
