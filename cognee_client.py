from __future__ import annotations

import io
import httpx

import config


class CogneeClient:
    """Async wrapper around the Cognee Cloud REST API."""

    def __init__(self) -> None:
        self.base_url = config.COGNEE_BASE_URL.rstrip("/")
        self.api_key = config.COGNEE_API_KEY
        self._timeout = httpx.Timeout(120.0, connect=30.0)

    def _headers(self) -> dict[str, str]:
        headers = {"X-Api-Key": self.api_key}
        if hasattr(config, "COGNEE_TENANT_ID") and config.COGNEE_TENANT_ID:
            headers["X-Tenant-Id"] = config.COGNEE_TENANT_ID
        return headers

    # ── remember ─────────────────────────────────────────────────────────

    async def remember(self, dataset_name: str, text_content: str) -> dict:
        """Upload text content as a file to the /remember endpoint."""
        try:
            buf = io.BytesIO(text_content.encode("utf-8"))
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/remember",
                    headers=self._headers(),
                    data={"datasetName": dataset_name},
                    files={"data": ("content.txt", buf, "text/plain")},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"Cognee remember failed ({exc.response.status_code}): {exc.response.text}"}
        except httpx.RequestError as exc:
            return {"error": f"Cognee remember request error: {str(exc)}"}

    # ── recall ───────────────────────────────────────────────────────────

    async def recall(
        self,
        dataset_name: str,
        query: str,
        search_type: str = "GRAPH_COMPLETION",
        top_k: int = 10,
    ) -> dict:
        """Query knowledge from the /recall endpoint."""
        try:
            payload = {
                "searchType": search_type,
                "datasets": [dataset_name],
                "query": query,
                "topK": top_k,
            }
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/recall",
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"Cognee recall failed ({exc.response.status_code}): {exc.response.text}"}
        except httpx.RequestError as exc:
            return {"error": f"Cognee recall request error: {str(exc)}"}

    # ── improve ──────────────────────────────────────────────────────────

    async def improve(self, dataset_name: str) -> dict:
        """Trigger knowledge graph improvement for a dataset."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/improve",
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={"datasets": [dataset_name]},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"Cognee improve failed ({exc.response.status_code}): {exc.response.text}"}
        except httpx.RequestError as exc:
            return {"error": f"Cognee improve request error: {str(exc)}"}

    # ── forget ───────────────────────────────────────────────────────────

    async def forget(self, dataset_name: str) -> dict:
        """Delete a dataset from Cognee."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/forget",
                    headers={**self._headers(), "Content-Type": "application/json"},
                    json={"dataset": dataset_name},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"Cognee forget failed ({exc.response.status_code}): {exc.response.text}"}
        except httpx.RequestError as exc:
            return {"error": f"Cognee forget request error: {str(exc)}"}

    # ── get_datasets ─────────────────────────────────────────────────────

    async def get_datasets(self) -> list[dict] | dict:
        """List all datasets."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/datasets",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"Cognee get_datasets failed ({exc.response.status_code}): {exc.response.text}"}
        except httpx.RequestError as exc:
            return {"error": f"Cognee get_datasets request error: {str(exc)}"}

    # ── get_graph ────────────────────────────────────────────────────────

    async def get_graph(self, dataset_id: str) -> dict:
        """Retrieve the knowledge graph for a specific dataset."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/datasets/{dataset_id}/graph",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            return {"error": f"Cognee get_graph failed ({exc.response.status_code}): {exc.response.text}"}
        except httpx.RequestError as exc:
            return {"error": f"Cognee get_graph request error: {str(exc)}"}

    # ── visualize ────────────────────────────────────────────────────────

    async def visualize(self, dataset_id: str) -> str:
        """Get HTML visualization for a dataset."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/visualize",
                    headers=self._headers(),
                    params={"dataset_id": dataset_id},
                )
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as exc:
            return f"<p>Cognee visualize failed ({exc.response.status_code}): {exc.response.text}</p>"
        except httpx.RequestError as exc:
            return f"<p>Cognee visualize request error: {str(exc)}</p>"


# Module-level singleton
cognee_client = CogneeClient()
