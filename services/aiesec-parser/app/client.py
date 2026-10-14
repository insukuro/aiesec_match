"""Клиент AIESEC GraphQL: троттлинг, ретраи, интроспекция схемы, авто-выбор полей."""
from __future__ import annotations

import json
import logging
import threading
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Iterator

import requests

log = logging.getLogger("aiesec.client")

SEARCH_FIELDS = ["searchOpportunities", "opportunities"]

# вложенные объекты -> какие поля из них берём (если есть в схеме)
NESTED_PREFERRED = {
    "home_lc": {"id", "name", "full_name", "tag"},
    "home_mc": {"id", "name", "full_name", "tag", "country_code"},
    "host_lc": {"id", "name", "full_name", "tag"},
    "city": {"id", "name"},
    "organisation": {"id", "name"},
    "programme": {"id", "short_name", "short_name_display", "name"},
    "branch": {"id", "name"},
    "currency": {"id", "name", "alphabetic_code"},
}
JSON_KEEP = {"project_fee", "work_hours", "fee_and_health_insurance", "opportunity_cost"}
LIST_OBJECT_FIELDS = {"skills", "backgrounds", "languages", "study_levels", "nationalities", "skills_developments"}
# лёгкий набор для сверки статусов
SLIM_FIELDS = ["id", "status", "current_status", "available_openings", "applicants_count",
               "accepted_count", "applications_close_date"]

TYPE_FRAG = "fragment T on __Type{kind name ofType{kind name ofType{kind name ofType{kind name}}}}"


class AiesecError(RuntimeError):
    pass


class AuthError(AiesecError):
    pass


class NotSupported(AiesecError):
    pass


class GQLError(AiesecError):
    def __init__(self, errors):
        super().__init__(json.dumps(errors, ensure_ascii=False)[:1500])
        self.errors = errors


def type_str(t: dict) -> str:
    if t["kind"] == "NON_NULL":
        return type_str(t["ofType"]) + "!"
    if t["kind"] == "LIST":
        return "[" + type_str(t["ofType"]) + "]"
    return t["name"]


def unwrap(t: dict) -> dict:
    while t.get("ofType"):
        t = t["ofType"]
    return t


def norm(s: Any) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return " ".join(s.split())


@dataclass
class SearchSchema:
    field: str  # searchOpportunities | opportunities
    args: dict[str, str]
    item_type: str
    filters: dict[str, dict]  # имя фильтра -> inputField


class AiesecClient:
    def __init__(self, token: str, url: str, per_page: int = 200, max_pages: int = 200,
                 delay: float = 0.7, timeout: int = 60, max_retries: int = 4,
                 exclude_fields: list[str] | None = None):
        self.token = token.strip()
        self.url = url
        self.per_page = per_page
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.broken_fields: set[str] = set(exclude_fields or [])

        # состояние авторизации: None — ещё не проверяли, True/False — по результату последнего запроса
        self.token_source = "env"
        self.auth_ok: bool | None = None
        self.auth_error: str | None = None
        self.auth_checked_at: datetime | None = None

        self._http = requests.Session()
        self._throttle_lock = threading.Lock()
        self._last_call = 0.0
        self._types: dict[str, dict] = {}
        self._qf: dict[str, dict] | None = None
        self._schema: SearchSchema | None = None
        self._select_cache: dict[tuple, str] = {}

    # ---------- транспорт ----------
    def _throttle(self) -> None:
        with self._throttle_lock:
            wait = self._last_call + self.delay - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()

    def gql(self, query: str, variables: dict | None = None) -> dict:
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self._throttle()
            try:
                r = self._http.post(
                    self.url,
                    params={"access_token": self.token},
                    headers={"Authorization": self.token, "Content-Type": "application/json"},
                    json={"query": query, "variables": variables or {}},
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                last_err = e
                self._backoff(attempt)
                continue
            if r.status_code in (401, 403):
                msg = f"{r.status_code}: токен не принят. {r.text[:300]}"
                self._mark_auth(False, msg)
                raise AuthError(msg)
            if r.status_code == 429 or r.status_code >= 500:
                last_err = AiesecError(f"HTTP {r.status_code}")
                retry_after = None
                try:
                    retry_after = float(r.headers.get("Retry-After", ""))
                except ValueError:
                    pass
                log.warning("AIESEC вернул %s, попытка %s/%s", r.status_code, attempt + 1, self.max_retries + 1)
                self._backoff(attempt, retry_after)
                continue
            r.raise_for_status()
            self._mark_auth(True)
            data = r.json()
            if data.get("errors"):
                raise GQLError(data["errors"])
            return data["data"]
        raise AiesecError(f"запрос не удался после ретраев: {last_err}")

    def _backoff(self, attempt: int, retry_after: float | None = None) -> None:
        time.sleep(retry_after if retry_after else min(2 ** attempt * 2, 60))

    # ---------- токен ----------
    def _mark_auth(self, ok: bool, error: str | None = None) -> None:
        self.auth_ok = ok
        self.auth_error = None if ok else error
        self.auth_checked_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def set_token(self, token: str, source: str = "api", verified: bool | None = None) -> None:
        """Подмена токена на лету. Кэши схемы не трогаем: схема от токена не зависит."""
        self.token = token.strip()
        self.token_source = source
        self.auth_ok = verified
        self.auth_error = None
        self.auth_checked_at = None

    def check_token(self, token: str | None = None) -> tuple[bool, str | None]:
        """Один дешёвый запрос. (True, None) / (False, ответ AIESEC). AiesecError — если AIESEC недоступен.
        Токен-кандидат не применяется; если проверяем текущий — обновляем состояние авторизации."""
        candidate = (token or self.token).strip()
        self._throttle()
        try:
            r = self._http.post(self.url, params={"access_token": candidate},
                                headers={"Authorization": candidate, "Content-Type": "application/json"},
                                json={"query": "{ __typename }"}, timeout=self.timeout)
        except requests.RequestException as e:
            raise AiesecError(f"AIESEC недоступен: {e}") from e
        if r.status_code == 429 or r.status_code >= 500:
            raise AiesecError(f"AIESEC ответил HTTP {r.status_code}, проверить токен не удалось")
        ok = r.status_code not in (401, 403)
        if candidate == self.token:
            self._mark_auth(ok, None if ok else f"{r.status_code}: {r.text[:300]}")
        return ok, (None if ok else r.text[:300])

    # ---------- интроспекция ----------
    def get_type(self, name: str) -> dict:
        if name not in self._types:
            q = ("query($n:String!){__type(name:$n){name kind "
                 "fields{name args{name type{...T}} type{...T}} "
                 "inputFields{name type{...T}} enumValues{name}}} " + TYPE_FRAG)
            self._types[name] = self.gql(q, {"n": name})["__type"]
        return self._types[name]

    def query_fields(self) -> dict[str, dict]:
        if self._qf is None:
            q = "{__schema{queryType{fields{name args{name type{...T}} type{...T}}}}} " + TYPE_FRAG
            self._qf = {f["name"]: f for f in self.gql(q)["__schema"]["queryType"]["fields"]}
        return self._qf

    @staticmethod
    def arg_types(field: dict) -> dict[str, str]:
        return {a["name"]: type_str(a["type"]) for a in field["args"]}

    def schema(self) -> SearchSchema:
        if self._schema:
            return self._schema
        qf = self.query_fields()
        fname = next((n for n in SEARCH_FIELDS if n in qf), None)
        if not fname:
            raise AiesecError("В схеме нет searchOpportunities/opportunities")
        field = qf[fname]
        args = self.arg_types(field)
        list_t = self.get_type(unwrap(field["type"])["name"])
        data = next((f for f in list_t["fields"] if f["name"] == "data"), None)
        if not data:
            raise AiesecError("В типе списка нет поля data")
        filters_t = self.get_type(args["filters"].rstrip("!"))
        self._schema = SearchSchema(
            field=fname, args=args, item_type=unwrap(data["type"])["name"],
            filters={f["name"]: f for f in filters_t["inputFields"]},
        )
        return self._schema

    def supports_range_filter(self, name: str) -> bool:
        """Есть ли фильтр `name` вида {from, to}."""
        f = self.schema().filters.get(name)
        if not f:
            return False
        base = unwrap(f["type"])
        if base["kind"] != "INPUT_OBJECT":
            return False
        return "from" in {x["name"] for x in self.get_type(base["name"])["inputFields"] or []}

    def _scalar_names(self, type_name: str) -> set[str]:
        return {f["name"] for f in self.get_type(type_name)["fields"]
                if unwrap(f["type"])["kind"] in ("SCALAR", "ENUM")}

    def _auto_select(self, type_name: str) -> str:
        parts = []
        for f in self.get_type(type_name)["fields"]:
            name = f["name"]
            if name in self.broken_fields:
                continue
            base = unwrap(f["type"])
            if base["kind"] == "ENUM":
                parts.append(name)
            elif base["kind"] == "SCALAR":
                if base["name"] == "JSON" and name not in JSON_KEEP:
                    continue
                parts.append(name)
            elif base["kind"] == "OBJECT" and name in NESTED_PREFERRED:
                sub = [sf["name"] for sf in self.get_type(base["name"])["fields"]
                       if sf["name"] in NESTED_PREFERRED[name] and sf["name"] not in self.broken_fields
                       and unwrap(sf["type"])["kind"] in ("SCALAR", "ENUM")]
                parts.append(f"{name}{{{' '.join(sub or ['id'])}}}")
            elif base["kind"] == "OBJECT" and name in LIST_OBJECT_FIELDS:
                sub = [sf["name"] for sf in self.get_type(base["name"])["fields"]
                       if unwrap(sf["type"])["kind"] in ("SCALAR", "ENUM")
                       and unwrap(sf["type"])["name"] != "JSON" and sf["name"] not in self.broken_fields]
                if sub:
                    parts.append(f"{name}{{{' '.join(sub)}}}")
        return " ".join(parts)

    def select(self, mode: str, type_name: str | None = None) -> str:
        type_name = type_name or self.schema().item_type
        key = (type_name, mode, frozenset(self.broken_fields))
        if key not in self._select_cache:
            if mode == "slim":
                have = self._scalar_names(type_name)
                self._select_cache[key] = " ".join(n for n in SLIM_FIELDS
                                                   if n in have and n not in self.broken_fields)
            else:
                self._select_cache[key] = self._auto_select(type_name)
        return self._select_cache[key]

    # ---------- запросы с авто-исключением «сломанных» полей ----------
    def _run(self, make_query: Callable[[], str], variables: dict, skip: set[str],
             extract: Callable[[dict], Any]) -> Any:
        for _ in range(20):
            try:
                return extract(self.gql(make_query(), variables))
            except GQLError as e:
                new = {err["path"][-1] for err in e.errors
                       if err.get("path") and isinstance(err["path"][-1], str)} - self.broken_fields - skip
                if not new:
                    raise
                self.broken_fields |= new
                self._select_cache.clear()
                log.warning("сервер не умеет поля %s — исключаю и повторяю", sorted(new))
        raise AiesecError("слишком много сломанных полей")

    def search_page(self, filters: dict, page: int, mode: str = "full") -> list[dict]:
        s = self.schema()

        def make_query() -> str:
            a = s.args
            return (f"query($page:{a.get('page', 'Int')},$per_page:{a.get('per_page', 'Int')},"
                    f"$filters:{a['filters']}){{ {s.field}(page:$page, per_page:$per_page, filters:$filters)"
                    f"{{ data {{ {self.select(mode)} }} }} }}")

        return self._run(make_query, {"page": page, "per_page": self.per_page, "filters": filters},
                         {s.field, "data"}, lambda d: d[s.field]["data"] or [])

    def iter_pages(self, filters: dict, mode: str = "full") -> Iterator[list[dict]]:
        """Отдаёт страницы. Если упёрлись в max_pages — ошибка (выдача неполная, закрывать по ней нельзя)."""
        for page in range(1, self.max_pages + 1):
            rows = self.search_page(filters, page, mode)
            log.info("стр. %s: %s (%s)", page, len(rows), mode)
            if rows:
                yield rows
            if len(rows) < self.per_page:
                return
        raise AiesecError(f"достигнут max_pages={self.max_pages}, выдача неполная")

    def get_opportunity(self, opportunity_id: int) -> dict | None:
        f = self.query_fields().get("opportunity")
        if not f:
            raise NotSupported("в схеме нет запроса opportunity(id)")
        id_type = self.arg_types(f).get("id", "ID!")
        type_name = unwrap(f["type"])["name"]

        def make_query() -> str:
            return f"query($id:{id_type}){{ opportunity(id:$id){{ {self.select('full', type_name)} }} }}"

        try:
            return self._run(make_query, {"id": opportunity_id}, {"opportunity"}, lambda d: d["opportunity"])
        except GQLError as e:
            if "not found" in str(e).lower():
                return None
            raise

    # ---------- офисы ----------
    def search_offices(self, q: str, limit: int = 50) -> list[dict]:
        query = ("query($q:String,$pp:Int){ committees(q:$q, per_page:$pp)"
                 "{ data { id name full_name tag country_code parent{ id name } } } }")
        return self.gql(query, {"q": q, "pp": limit})["committees"]["data"] or []