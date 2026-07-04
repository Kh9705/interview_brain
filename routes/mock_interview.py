from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from database import get_db
from models import (
    MockInterviewEvaluateRequest,
    MockInterviewEvaluateResponse,
    MockInterviewHistoryItem,
    MockInterviewStartRequest,
    MockInterviewStartResponse,
)

router = APIRouter(prefix="/api", tags=["mock_interview"])


def _extract_answer_text(result) -> str:
    """Normalise a Cognee recall result into a plain string."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        return result.get("answer", result.get("response", result.get("content", str(result))))
    if isinstance(result, list):
        parts = []
        for item in result:
            if isinstance(item, dict):
                parts.append(item.get("content", item.get("text", str(item))))
            else:
                parts.append(str(item))
        return "\n\n".join(parts)
    return str(result)


def _parse_questions(raw: str, num_questions: int) -> list[str]:
    """Best-effort extraction of numbered questions from free-form text."""
    # Try numbered pattern: "1. ...", "1) ..."
    pattern = re.compile(r"(?:^|\n)\s*\d+[\.\)]\s*(.+?)(?=\n\s*\d+[\.\)]|\Z)", re.DOTALL)
    matches = pattern.findall(raw)
    if matches:
        return [m.strip() for m in matches[:num_questions]]
    # Fallback: split on newlines and take non-empty lines
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]
    if lines:
        return lines[:num_questions]
    # Last resort: return the whole text as one question
    return [raw.strip()]


def _parse_score(raw: str) -> float:
    """Extract a numeric score from evaluator text. Defaults to 5.0."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*10", raw)
    if match:
        return min(float(match.group(1)), 10.0)
    match = re.search(r"[Ss]core[:\s]*(\d+(?:\.\d+)?)", raw)
    if match:
        return min(float(match.group(1)), 10.0)
    return 5.0


# ── Start a mock interview ──────────────────────────────────────────────────

@router.post("/mock-interview/start", response_model=MockInterviewStartResponse)
async def start_mock_interview(
    body: MockInterviewStartRequest,
    user: dict = Depends(get_current_user),
):
    try:
        user_id = user["id"]
        role = user.get("role", "Software Engineer")
        company_key = body.company.lower().strip().replace(" ", "_")
        company_dataset = f"{user_id}_{company_key}"

        query = (
            f"Generate exactly {body.num_questions} unique interview questions for a "
            f"{role} position at {body.company}. "
            f"Include a mix of coding, system design, and behavioral questions. "
            f"Number each question."
        )

        result = await cognee_client.recall(company_dataset, query)
        if isinstance(result, dict) and "error" in result:
            # Fallback to profile dataset
            profile_dataset = f"{user_id}_profile"
            result = await cognee_client.recall(profile_dataset, query)

        raw_text = _extract_answer_text(result)
        questions = _parse_questions(raw_text, body.num_questions)

        # Persist interview session
        interview_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        db = await get_db()

        await db.execute(
            """INSERT INTO mock_interviews (id, user_id, company, role, overall_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (interview_id, user_id, body.company, role, 0.0, now),
        )

        for idx, q in enumerate(questions, start=1):
            q_id = str(uuid4())
            await db.execute(
                """INSERT INTO mock_questions (id, interview_id, question_number, question, answer, score, feedback)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (q_id, interview_id, idx, q, "", 0.0, ""),
            )

        await db.commit()

        return MockInterviewStartResponse(
            interview_id=interview_id,
            company=body.company,
            role=role,
            questions=questions,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ── Evaluate an answer ───────────────────────────────────────────────────────

@router.post("/mock-interview/evaluate", response_model=MockInterviewEvaluateResponse)
async def evaluate_answer(
    body: MockInterviewEvaluateRequest,
    user: dict = Depends(get_current_user),
):
    try:
        user_id = user["id"]
        db = await get_db()

        # Verify the interview belongs to this user
        cursor = await db.execute(
            "SELECT company, role FROM mock_interviews WHERE id = ? AND user_id = ?",
            (body.interview_id, user_id),
        )
        interview = await cursor.fetchone()
        if interview is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")

        company_key = interview["company"].lower().strip().replace(" ", "_")
        company_dataset = f"{user_id}_{company_key}"

        eval_query = (
            f"Evaluate the following interview answer on a scale of 1-10. "
            f"Provide a score out of 10 and detailed feedback.\n\n"
            f"Company: {interview['company']}\n"
            f"Role: {interview['role']}\n"
            f"Question: {body.question}\n"
            f"Candidate's Answer: {body.answer}\n\n"
            f"Provide the score as 'Score: X/10' followed by constructive feedback."
        )

        result = await cognee_client.recall(company_dataset, eval_query)
        if isinstance(result, dict) and "error" in result:
            profile_dataset = f"{user_id}_profile"
            result = await cognee_client.recall(profile_dataset, eval_query)

        raw_text = _extract_answer_text(result)
        score = _parse_score(raw_text)

        # Update the question record
        await db.execute(
            """UPDATE mock_questions
               SET answer = ?, score = ?, feedback = ?
               WHERE interview_id = ? AND question_number = ?""",
            (body.answer, score, raw_text, body.interview_id, body.question_number),
        )

        # Recalculate overall score
        cursor = await db.execute(
            "SELECT AVG(score) as avg_score FROM mock_questions WHERE interview_id = ? AND score > 0",
            (body.interview_id,),
        )
        avg_row = await cursor.fetchone()
        overall = avg_row["avg_score"] if avg_row and avg_row["avg_score"] else 0.0

        await db.execute(
            "UPDATE mock_interviews SET overall_score = ? WHERE id = ?",
            (overall, body.interview_id),
        )
        await db.commit()

        return MockInterviewEvaluateResponse(
            interview_id=body.interview_id,
            question_number=body.question_number,
            score=score,
            feedback=raw_text,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ── History ──────────────────────────────────────────────────────────────────

@router.get("/mock-interview/history", response_model=list[MockInterviewHistoryItem])
async def interview_history(user: dict = Depends(get_current_user)):
    try:
        db = await get_db()
        cursor = await db.execute(
            """SELECT id, company, role, overall_score, created_at
               FROM mock_interviews
               WHERE user_id = ?
               ORDER BY created_at DESC""",
            (user["id"],),
        )
        interviews = await cursor.fetchall()

        results: list[MockInterviewHistoryItem] = []
        for irow in interviews:
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
            results.append(
                MockInterviewHistoryItem(
                    id=irow["id"],
                    company=irow["company"],
                    role=irow["role"],
                    overall_score=irow["overall_score"],
                    created_at=irow["created_at"],
                    questions=questions,
                )
            )

        return results

    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
