import httpx

from .config import get_settings
from .errors import MatcherRejected, MatcherTimeout, MatcherUnavailable
from fastapi import Request


class MatcherClient:
    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(
            base_url=s.matcher_base_url, timeout=s.matcher_timeout_s,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def match(self, payload: dict) -> dict:
        try:
            r = await self._client.post("/v1/match", json=payload)
        except httpx.TimeoutException as e:
            raise MatcherTimeout() from e
        except httpx.HTTPError as e:
            raise MatcherUnavailable(str(e)) from e

        if r.status_code >= 500:
            # matcher вернул 500 — не наш клиент виноват, это outage
            raise MatcherUnavailable(f"matcher {r.status_code}: {r.text[:200]}")

        if r.status_code >= 400:
            try:
                detail = r.json()
            except ValueError:
                detail = r.text
            raise MatcherRejected(r.status_code, detail)

        try:
            return r.json()
        except ValueError as e:
            raise MatcherUnavailable("invalid json from matcher") from e


def get_matcher(request: Request) -> MatcherClient:
    return request.app.state.matcher