from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class TokenIn(BaseModel):
    token: str | None = Field(
        None, min_length=10, max_length=2000,
        description="Готовый access_token (живёт ~2 ч; без refresh-настроек сам не обновится)",
    )
    refresh_token: str | None = Field(
        None, min_length=10, max_length=2000,
        description="refresh_token: меняется на access_token, дальше сервис обновляет токен сам",
    )
    verify: bool = Field(True, description="Для token: проверить запросом к AIESEC до применения")
    run_sync: bool = Field(
        True,
        description="Если синк падал из-за токена (или первого синка ещё не было) — запустить сразу",
    )

    @model_validator(mode="after")
    def _exactly_one(self):
        if bool(self.token) == bool(self.refresh_token):
            raise ValueError("Передайте ровно одно из полей: token или refresh_token")
        return self