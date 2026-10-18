from __future__ import annotations

import logging
from collections import Counter

from ..client import AiesecClient, NotSupported
from ..models import utcnow
from .ingest import Ingestor

log = logging.getLogger("aiesec.sync.gapfill")


def gap_fill(
    client: AiesecClient, ingestor: Ingestor, ids: set[int],
    stats: Counter, full_run,
) -> None:
    if len(ids) <= ingestor.settings.gap_fill_max:
        try:
            with ingestor.Session() as s:
                now = utcnow()
                for oid in ids:
                    raw = client.get_opportunity(oid)
                    if raw:
                        stats[ingestor.upsert_one(s, raw, "gap_fill", True, now.date(), now)] += 1
                s.commit()
            stats["gap_fill"] = "by_id"
            return
        except NotSupported:
            log.warning("opportunity(id) недоступен — догружаю полным проходом")
    stats["gap_fill"] = "full_scan"
    full_run(stats)