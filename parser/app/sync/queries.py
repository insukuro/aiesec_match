from __future__ import annotations

import logging

from ..client import AiesecClient, AiesecError
from ..config import Targets

log = logging.getLogger("aiesec.sync.queries")


def build_queries(client: AiesecClient, targets: Targets, extra: dict | None = None) -> list[tuple[str, dict]]:
    known = client.schema().filters
    out = []
    for name, geo in targets.geo_queries():
        bad_geo = [k for k in geo if k not in known]
        if bad_geo:
            raise AiesecError(f"Схема не поддерживает гео-фильтры {bad_geo}")
        filters = {**targets.base_filters, **(extra or {}), **geo}
        for k in [k for k in filters if k not in known]:
            log.warning("фильтр '%s' не поддерживается схемой — отбрасываю", k)
            filters.pop(k)
        out.append((name, filters))
    if not out:
        raise AiesecError("В targets.json нет ни стран, ни городов")
    return out