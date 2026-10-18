"""Регрессия OpenAPI: набор рутей и их параметры не должны меняться случайно."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import main


SNAPSHOT = Path(__file__).resolve().parents[2] / "docs" / "openapi.json"


def _shape(spec: dict) -> dict:
    return {
        path: {
            method: {
                "params": sorted(
                    (p.get("name"), p.get("in")) for p in op.get("parameters", [])
                ),
                "responses": sorted(op.get("responses", {}).keys()),
            }
            for method, op in ops.items()
        }
        for path, ops in spec["paths"].items()
    }


def test_openapi_matches_snapshot():
    current = _shape(main.app.openapi())
    if not SNAPSHOT.exists():
        SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(current, indent=2, ensure_ascii=False))
        pytest.skip(f"snapshot created: {SNAPSHOT}")
    expected = json.loads(SNAPSHOT.read_text())
    assert current == expected