from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from models import CompareRequest, CompareResponse

router = APIRouter(prefix="/api", tags=["compare"])


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


@router.post("/compare", response_model=CompareResponse)
async def compare_companies(body: CompareRequest, user: dict = Depends(get_current_user)):
    """Compare interview requirements between two companies."""
    try:
        user_id = user["id"]
        role = user.get("role", "Software Engineer")

        company1_key = body.company1.lower().strip().replace(" ", "_")
        company2_key = body.company2.lower().strip().replace(" ", "_")
        dataset1 = f"{user_id}_{company1_key}"
        dataset2 = f"{user_id}_{company2_key}"

        # Query each company's interview requirements
        query_template = (
            "What are the key interview requirements, typical questions, "
            "required skills, and preparation focus areas for a {role} position at {company}? "
            "Include technical skills, system design expectations, and behavioral competencies."
        )

        result1 = await cognee_client.recall(
            dataset1, query_template.format(role=role, company=body.company1)
        )
        result2 = await cognee_client.recall(
            dataset2, query_template.format(role=role, company=body.company2)
        )

        # Fallback to profile dataset if company datasets error
        profile_dataset = f"{user_id}_profile"
        if isinstance(result1, dict) and "error" in result1:
            result1 = await cognee_client.recall(
                profile_dataset,
                query_template.format(role=role, company=body.company1),
            )
        if isinstance(result2, dict) and "error" in result2:
            result2 = await cognee_client.recall(
                profile_dataset,
                query_template.format(role=role, company=body.company2),
            )

        text1 = _extract_text(result1)
        text2 = _extract_text(result2)

        # Generate comparison via profile dataset
        comparison_query = (
            f"Compare the interview processes of {body.company1} and {body.company2} "
            f"for a {role} role. Highlight similarities, differences, unique requirements, "
            f"and provide a skill match percentage estimate for the candidate based on "
            f"their profile and weak areas. Format the comparison clearly."
        )
        comparison_result = await cognee_client.recall(profile_dataset, comparison_query)
        comparison_text = _extract_text(comparison_result)

        return CompareResponse(
            company1=body.company1,
            company2=body.company2,
            company1_requirements=text1,
            company2_requirements=text2,
            comparison=comparison_text,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
