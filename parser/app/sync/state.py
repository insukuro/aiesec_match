from __future__ import annotations

from sqlalchemy.orm import sessionmaker

from ..models import SyncState


class StateStore:
    def __init__(self, session_factory: sessionmaker):
        self.Session = session_factory

    def get(self, key: str) -> str | None:
        with self.Session() as s:
            row = s.get(SyncState, key)
            return row.value if row else None

    def set(self, key: str, value: str) -> None:
        with self.Session() as s:
            s.merge(SyncState(key=key, value=value))
            s.commit()

    def set_many(self, items: dict[str, str]) -> None:
        with self.Session() as s:
            for k, v in items.items():
                s.merge(SyncState(key=k, value=v))
            s.commit()