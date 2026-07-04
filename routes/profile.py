from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import get_db
from models import ProfileResponse, UserOut

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    """Return the user's profile, feedback summary, and mock interview history."""
    try:
        db = await get_db()
        user_id = user["id"]

        # ── User ─────────────────────────────────────────────────────────
        user_out = UserOut(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            companies=user["companies"],
            weak_areas=user["weak_areas"],
            created_at=user["created_at"],
        )

        # ── Feedback summary (aggregate by company + topic) ──────────────
        cursor = await db.execute(
            """SELECT company, topic, result, COUNT(*) as count
               FROM feedback
               WHERE user_id = ?
               GROUP BY company, topic, result
               ORDER BY company, topic""",
            (user_id,),
        )
        feedback_rows = await cursor.fetchall()
        feedback_summary = [
            {
                "company": row["company"],
                "topic": row["topic"],
                "result": row["result"],
                "count": row["count"],
            }
            for row in feedback_rows
        ]

        # ── Mock interview history ───────────────────────────────────────
        cursor = await db.execute(
            """SELECT mi.id, mi.company, mi.role, mi.overall_score, mi.created_at
               FROM mock_interviews mi
               WHERE mi.user_id = ?
               ORDER BY mi.created_at DESC
               LIMIT 20""",
            (user_id,),
        )
        interview_rows = await cursor.fetchall()

        mock_history: list[dict] = []
        for irow in interview_rows:
            q_cursor = await db.execute(
                """SELECT question_number, question, answer, score, feedback
                   FROM mock_questions
                   WHERE interview_id = ?
                   ORDER BY question_number""",
                (irow["id"],),
            )
            q_rows = await q_cursor.fetchall()
            questions = [
                {
                    "question_number": q["question_number"],
                    "question": q["question"],
                    "answer": q["answer"],
                    "score": q["score"],
                    "feedback": q["feedback"],
                }
                for q in q_rows
            ]
            mock_history.append(
                {
                    "id": irow["id"],
                    "company": irow["company"],
                    "role": irow["role"],
                    "overall_score": irow["overall_score"],
                    "created_at": irow["created_at"],
                    "questions": questions,
                }
            )

        return ProfileResponse(
            user=user_out,
            feedback_summary=feedback_summary,
            mock_interview_history=mock_history,
        )

    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
