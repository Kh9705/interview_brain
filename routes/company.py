from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from database import get_db
from models import CompanyDeleteResponse

router = APIRouter(prefix="/api", tags=["company"])


@router.delete("/company/{name}", response_model=CompanyDeleteResponse)
async def delete_company(name: str, user: dict = Depends(get_current_user)):
    """Remove a company from the user's list and forget the associated Cognee dataset."""
    try:
        user_id = user["id"]
        companies: list[str] = user.get("companies", [])

        # Find the company (case-insensitive match)
        matched: str | None = None
        for c in companies:
            if c.lower().strip() == name.lower().strip():
                matched = c
                break

        if matched is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Company '{name}' not found in your company list",
            )

        # Remove from list
        companies.remove(matched)

        # Update SQLite
        db = await get_db()
        await db.execute(
            "UPDATE users SET companies = ? WHERE id = ?",
            (json.dumps(companies), user_id),
        )
        await db.commit()

        # Forget the company dataset in Cognee
        company_key = matched.lower().strip().replace(" ", "_")
        company_dataset = f"{user_id}_{company_key}"
        await cognee_client.forget(company_dataset)

        return CompanyDeleteResponse(
            message=f"Company '{matched}' removed and dataset forgotten",
            company=matched,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
