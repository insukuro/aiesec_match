# backend/tests/test_matcher_client.py
import httpx
import pytest

from app.errors import MatcherRejected, MatcherTimeout, MatcherUnavailable
from app.infrastructure.matcher_client import MatcherClient


def _client_with(handler) -> MatcherClient:
    c = MatcherClient.__new__(MatcherClient)  # без __init__ (не читаем settings)
    c._client = httpx.AsyncClient(
        base_url="http://matcher:8000", transport=httpx.MockTransport(handler)
    )
    return c


@pytest.mark.asyncio
async def test_ok():
    c = _client_with(lambda req: httpx.Response(200, json={"groups": []}))
    try:
        assert await c.match({}) == {"groups": []}
    finally:
        await c.aclose()


@pytest.mark.asyncio
async def test_5xx_becomes_unavailable():
    c = _client_with(lambda req: httpx.Response(503, text="boom"))
    try:
        with pytest.raises(MatcherUnavailable):
            await c.match({})
    finally:
        await c.aclose()


@pytest.mark.asyncio
async def test_4xx_becomes_rejected():
    c = _client_with(lambda req: httpx.Response(422, json={"detail": "bad"}))
    try:
        with pytest.raises(MatcherRejected) as ei:
            await c.match({})
        assert ei.value.status_code == 422
    finally:
        await c.aclose()


@pytest.mark.asyncio
async def test_timeout():
    def handler(req):
        raise httpx.TimeoutException("slow")
    c = _client_with(handler)
    try:
        with pytest.raises(MatcherTimeout):
            await c.match({})
    finally:
        await c.aclose()


@pytest.mark.asyncio
async def test_invalid_json():
    c = _client_with(lambda req: httpx.Response(200, text="not json"))
    try:
        with pytest.raises(MatcherUnavailable, match="invalid json"):
            await c.match({})
    finally:
        await c.aclose()