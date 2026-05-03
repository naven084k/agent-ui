import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any

import httpx

from ..config import get_settings


class OpenAIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url.rstrip("/")
        self.default_model = settings.default_model

    def _headers(self) -> dict[str, str]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def list_models(self) -> list[dict[str, Any]]:
        if not self.api_key:
            return [{"name": self.default_model}]

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.base_url}/models", headers=self._headers())
            response.raise_for_status()

        models = response.json().get("data", [])
        items: list[dict[str, Any]] = []
        for model in sorted(models, key=lambda item: item.get("id", "")):
            model_id = model.get("id")
            if not model_id:
                continue
            created = model.get("created")
            modified_at = None
            if isinstance(created, int):
                modified_at = datetime.fromtimestamp(created, tz=UTC).isoformat()
            items.append({"name": model_id, "modified_at": modified_at})
        return items or [{"name": self.default_model}]

    async def chat_once(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "model": payload["model"],
            "messages": payload["messages"],
            "stream": False,
        }
        if payload.get("tools"):
            body["tools"] = payload["tools"]
            body["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            )
            response.raise_for_status()
            return response.json()

    async def chat_stream(self, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        body = {
            "model": payload["model"],
            "messages": payload["messages"],
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=body,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.removeprefix("data:").strip()
                    if data == "[DONE]":
                        yield {"done": True}
                        break

                    chunk = json.loads(data)
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield {"message": {"content": content}}


openai = OpenAIClient()
