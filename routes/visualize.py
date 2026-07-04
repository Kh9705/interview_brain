from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from cognee_client import cognee_client
from models import VisualizeResponse

router = APIRouter(prefix="/api", tags=["visualize"])


@router.get("/visualize", response_model=VisualizeResponse)
async def visualize_graph(user: dict = Depends(get_current_user)):
    """Return the knowledge graph nodes and edges for the user's profile dataset."""
    try:
        user_id = user["id"]

        # 1. List all datasets and find the user's profile dataset
        datasets = await cognee_client.get_datasets()

        if isinstance(datasets, dict) and "error" in datasets:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=datasets["error"],
            )

        profile_name = f"{user_id}_profile"
        profile_dataset_id: str | None = None

        if isinstance(datasets, list):
            for ds in datasets:
                ds_name = ds.get("name", "")
                if ds_name == profile_name:
                    profile_dataset_id = ds.get("id")
                    break

        if profile_dataset_id is None:
            return VisualizeResponse(nodes=[], edges=[])

        # 2. Fetch the graph
        graph_data = await cognee_client.get_graph(profile_dataset_id)

        if isinstance(graph_data, dict) and "error" in graph_data:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=graph_data["error"],
            )

        # Normalise: the graph endpoint may return {nodes: [...], edges: [...]}
        # or a list of nodes/edges.
        nodes: list[dict] = []
        edges: list[dict] = []

        if isinstance(graph_data, dict):
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
        elif isinstance(graph_data, list):
            # Some Cognee versions return a flat list of graph elements
            for item in graph_data:
                if isinstance(item, dict):
                    if "source" in item or "target" in item:
                        edges.append(item)
                    else:
                        nodes.append(item)

        return VisualizeResponse(nodes=nodes, edges=edges)

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
