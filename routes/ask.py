from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from models import AskRequest, AskResponse

router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, user: dict = Depends(get_current_user)):
    """Ask a question against the user's profile knowledge graph."""
    try:
        user_id = user["id"]
        profile_dataset = f"{user_id}_profile"

        result = await cognee_client.recall(profile_dataset, body.question)

        if isinstance(result, dict) and "error" in result:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=result["error"],
            )

        # The recall endpoint may return different shapes; normalise to a string answer.
        if isinstance(result, str):
            answer = result
        elif isinstance(result, dict):
            answer = result.get("answer", result.get("response", str(result)))
        elif isinstance(result, list):
            # Join multiple results into a single coherent answer
            parts = []
            for item in result:
                if isinstance(item, dict):
                    parts.append(item.get("content", item.get("text", str(item))))
                else:
                    parts.append(str(item))
            answer = "\n\n".join(parts)
        else:
            answer = str(result)

        return AskResponse(answer=answer)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
