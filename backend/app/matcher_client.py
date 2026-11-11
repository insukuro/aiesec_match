import httpx
from .config import get_settings
from .errors import MatcherTimeout, MatcherUnavailable


class MatcherClient:
    def __init__(self) -> None:
        s = get_settings()
        self._client = httpx.AsyncClient(base_url=s.matcher_base_url, timeout=s.matcher_timeout_s)

    async def match(self, payload: dict) -> dict:
        try:
            r = await self._client.post("/v1/match", json=payload)
        except httpx.TimeoutException as e:
            raise MatcherTimeout() from e
        except httpx.HTTPError as e:
            raise MatcherUnavailable(str(e)) from e
        if r.status_code >= 500:
            raise MatcherUnavailable(f"matcher {r.status_code}")
        r.raise_for_status()
        return r.json()


def get_matcher() -> MatcherClient:
    return MatcherClient()