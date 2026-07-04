from __future__ import annotations

import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import get_db
from cognee_client import cognee_client
from models import RoadmapRequest, RoadmapResponse, RoadmapOut, RoadmapUpdateRequest, RoadmapListResponse

router = APIRouter(prefix="/api", tags=["roadmap"])


def _extract_text(result) -> str:
    """Normalise Cognee recall output to a string."""
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


@router.post("/roadmap", response_model=RoadmapResponse)
async def generate_roadmap(body: RoadmapRequest, user: dict = Depends(get_current_user)):
    """Generate a day-by-day interview prep roadmap for a company and save it."""
    try:
        user_id = user["id"]
        role = user.get("role", "Software Engineer")
        weak_areas = user.get("weak_areas", [])
        weak_areas_str = ", ".join(weak_areas) if weak_areas else "general interview skills"

        company_key = body.company.lower().strip().replace(" ", "_")
        company_dataset = f"{user_id}_{company_key}"
        profile_dataset = f"{user_id}_profile"

        roadmap_query = (
            f"Create a detailed {body.days}-day interview preparation roadmap "
            f"for a {role} position at {body.company}. "
            f"The candidate's weak areas are: {weak_areas_str}. "
            f"Structure it strictly as a day-by-day plain text list. DO NOT use Markdown tables (no '|' characters). "
            f"For each day, write a heading like '### Day X' followed by a Markdown checklist. "
            f"FOR EVERY TASK, format it EXACTLY as a markdown checklist item starting with '- [ ] ' (e.g. '- [ ] Review HashMaps'). "
            f"Cover:\n"
            f"- Data structures and algorithms practice\n"
            f"- System design study\n"
            f"- Behavioral interview preparation\n"
            f"- Company-specific preparation\n"
            f"- Mock interview sessions\n"
            f"- Review and rest days\n\n"
            f"Prioritize the candidate's weak areas early in the plan. "
            f"Include specific topics, resources, and daily goals. DO NOT USE TABLES."
        )

        # Try company dataset first, fall back to profile
        result = await cognee_client.recall(company_dataset, roadmap_query)
        if isinstance(result, dict) and "error" in result:
            result = await cognee_client.recall(profile_dataset, roadmap_query)

        roadmap_text = _extract_text(result)

        # Save to DB
        db = await get_db()
        roadmap_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        
        title = f"{body.company} {body.days}-Day Roadmap"

        await db.execute(
            "INSERT INTO roadmaps (id, user_id, company, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (roadmap_id, user_id, title, roadmap_text, now),
        )
        await db.commit()

        roadmap_out = RoadmapOut(
            id=roadmap_id,
            user_id=user_id,
            company=title,
            content=roadmap_text,
            created_at=now
        )

        return RoadmapResponse(roadmap=roadmap_out)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/roadmap", response_model=RoadmapListResponse)
async def list_roadmaps(user: dict = Depends(get_current_user)):
    """Get all saved roadmaps for the current user."""
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM roadmaps WHERE user_id = ? ORDER BY created_at DESC", 
        (user["id"],)
    )
    rows = await cursor.fetchall()
    
    roadmaps = []
    for row in rows:
        roadmaps.append(RoadmapOut(
            id=row["id"],
            user_id=row["user_id"],
            company=row["company"],
            content=row["content"],
            created_at=row["created_at"]
        ))
        
    return RoadmapListResponse(roadmaps=roadmaps)


@router.put("/roadmap/{roadmap_id}", response_model=RoadmapOut)
async def update_roadmap(roadmap_id: str, body: RoadmapUpdateRequest, user: dict = Depends(get_current_user)):
    """Update a saved roadmap's content (e.g. checking off tasks)."""
    db = await get_db()
    
    # Verify ownership
    cursor = await db.execute("SELECT * FROM roadmaps WHERE id = ? AND user_id = ?", (roadmap_id, user["id"]))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found")
        
    await db.execute(
        "UPDATE roadmaps SET content = ? WHERE id = ?",
        (body.content, roadmap_id)
    )
    await db.commit()
    
    return RoadmapOut(
        id=row["id"],
        user_id=row["user_id"],
        company=row["company"],
        content=body.content,
        created_at=row["created_at"]
    )
