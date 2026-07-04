from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from database import get_db
from models import IngestRequest, IngestResponse

router = APIRouter(prefix="/api", tags=["ingest"])

# Map of well-known companies to their typical interview focus areas.
COMPANY_INTERVIEW_PROFILES: dict[str, str] = {
    "google": (
        "Google interviews focus on data structures and algorithms, system design, "
        "behavioral questions using the STAR method, coding in Python/Java/C++, "
        "dynamic programming, graph algorithms, distributed systems, and Googleyness."
    ),
    "amazon": (
        "Amazon interviews revolve around the 16 Leadership Principles, system design, "
        "object-oriented design, scalability, behavioral questions with STAR format, "
        "coding problems involving arrays, trees, and graphs, and AWS services knowledge."
    ),
    "meta": (
        "Meta (Facebook) interviews focus on coding (arrays, strings, graphs, dynamic programming), "
        "system design (news feed, messenger, distributed storage), behavioral questions, "
        "and product sense for PM roles. Fast-paced 45-minute coding rounds."
    ),
    "apple": (
        "Apple interviews emphasize domain-specific knowledge, system design, coding challenges, "
        "creativity and passion for Apple products, team collaboration, and problem-solving "
        "with a focus on user experience and attention to detail."
    ),
    "microsoft": (
        "Microsoft interviews cover data structures, algorithms, system design, "
        "behavioral questions, coding in C#/Java/Python, object-oriented design, "
        "Azure cloud services, and collaboration scenarios."
    ),
    "netflix": (
        "Netflix interviews focus on culture fit (Freedom & Responsibility), system design "
        "for streaming at scale, distributed systems, microservices architecture, "
        "data engineering, and senior-level leadership questions."
    ),
}


def _build_company_text(company: str, role: str) -> str:
    """Build a rich description of a company's interview process."""
    key = company.lower().strip()
    base = COMPANY_INTERVIEW_PROFILES.get(key)
    if base:
        return (
            f"Company: {company}\n"
            f"Target Role: {role}\n\n"
            f"Interview Profile:\n{base}\n\n"
            f"Candidates targeting {company} for a {role or 'software engineering'} role "
            f"should prepare for technical coding rounds, system design interviews, "
            f"and behavioral rounds. Key areas include problem-solving efficiency, "
            f"communication skills, and domain expertise."
        )
    # Generic fallback for any company
    return (
        f"Company: {company}\n"
        f"Target Role: {role}\n\n"
        f"Interview Profile:\n"
        f"{company} typically conducts multi-round interviews including: "
        f"phone screening, technical coding rounds, system design, "
        f"behavioral interviews, and a hiring committee review. "
        f"Candidates should prepare data structures, algorithms, "
        f"system design fundamentals, and practice articulating past experiences "
        f"using the STAR method."
    )


@router.post("/ingest", response_model=IngestResponse)
async def ingest(body: IngestRequest, user: dict = Depends(get_current_user)):
    try:
        user_id = user["id"]
        datasets_created: list[str] = []

        # 1. Build and store user profile dataset
        profile_dataset = f"{user_id}_profile"
        profile_text = (
            f"Candidate Profile\n"
            f"Name: {body.name}\n"
            f"Target Role: {body.role}\n"
            f"Target Companies: {', '.join(body.companies)}\n"
            f"Self-identified Weak Areas: {', '.join(body.weak_areas)}\n\n"
            f"This candidate is preparing for software engineering interviews. "
            f"They should focus on strengthening: {', '.join(body.weak_areas) if body.weak_areas else 'general interview skills'}."
        )
        await cognee_client.remember(profile_dataset, profile_text)
        datasets_created.append(profile_dataset)

        # 2. Store company-specific datasets
        for company in body.companies:
            company_key = company.lower().strip().replace(" ", "_")
            company_dataset = f"{user_id}_{company_key}"
            company_text = _build_company_text(company, body.role)
            await cognee_client.remember(company_dataset, company_text)
            datasets_created.append(company_dataset)

        # 3. Update user record in SQLite
        db = await get_db()
        await db.execute(
            "UPDATE users SET role = ?, companies = ?, weak_areas = ?, name = ? WHERE id = ?",
            (
                body.role,
                json.dumps(body.companies),
                json.dumps(body.weak_areas),
                body.name,
                user_id,
            ),
        )
        await db.commit()

        return IngestResponse(
            message="Profile and company data ingested successfully",
            datasets_created=datasets_created,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
