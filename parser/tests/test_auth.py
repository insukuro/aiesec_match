"""Автообновление токена: обмен refresh_token, проактивное и реактивное обновление, гонки, настройки."""
import json
import threading
import time
from datetime import timedelta

import pytest
import requests

from app.auth import OAuthRefresher, TokenSet, utcnow
from app.client import AiesecClient
from app.config import Settings
from app.errors import AiesecError, AuthError


class Resp:
    def __init__(self, status=200, body=None, text=None, headers=None):
        self.status_code = status
        self.text = text if text is not None else json.dumps(body if body is not None else {})
        self.headers = headers or {}

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


# ---------------- OAuthRefresher ----------------
class FakeSession:
    def __init__(self, *responses):
        self.responses, self.calls = list(responses), []

    def post(self, url, **kw):
        self.calls.append((url, kw))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def oauth(*responses):
    s = FakeSession(*responses)
    return OAuthRefresher("https://auth.example/oauth/token", "cid", "sec", origin="https://aiesec.org", session=s), s


def test_refresh_request_matches_the_curl_that_works():
    body = {"access_token": "A", "token_type": "Bearer", "expires_in": 7200, "refresh_token": "R2",
            "scope": "public", "created_at": int(time.time())}
    r, s = oauth(Resp(200, body))
    ts = r.refresh("R1")
    url, kw = s.calls[0]
    assert url == "https://auth.example/oauth/token"
    assert kw["auth"] == ("cid", "sec")                                             # curl -u id:secret
    assert kw["data"] == {"grant_type": "refresh_token", "refresh_token": "R1"}    # form-urlencoded
    assert kw["headers"]["Origin"] == "https://aiesec.org"
    assert ts.access_token == "A" and ts.refresh_token == "R2" and ts.scope == "public"
    assert abs((ts.expires_at - utcnow()).total_seconds() - 7200) < 5


def test_expiry_falls_back_to_local_clock_when_server_clock_is_off():
    body = {"access_token": "A", "expires_in": 7200, "created_at": int(time.time()) - 100_000}
    ts = oauth(Resp(200, body))[0].refresh("R1")
    assert abs((ts.expires_at - utcnow()).total_seconds() - 7200) < 5


def test_missing_expires_in_gives_unknown_expiry():
    assert oauth(Resp(200, {"access_token": "A"}))[0].refresh("R1").expires_at is None


def test_rejected_refresh_token_is_auth_error():
    r, _ = oauth(Resp(400, text='{"error":"invalid_grant"}'))
    with pytest.raises(AuthError) as e:
        r.refresh("dead")
    assert "invalid_grant" in str(e.value) and "PUT /admin/token" in str(e.value)


@pytest.mark.parametrize("resp", [Resp(503, text="oops"), requests.ConnectionError("dns"), Resp(200, text="<html>")])
def test_transient_or_garbage_is_not_auth_error(resp):
    with pytest.raises(AiesecError) as e:
        oauth(resp)[0].refresh("R1")
    assert not isinstance(e.value, AuthError)


# ---------------- AiesecClient ----------------
class ScriptedRefresher:
    def __init__(self, *results):
        self.results, self.calls = list(results), []

    def refresh(self, rt):
        self.calls.append(rt)
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class GqlHttp:
    def __init__(self, valid=(), bad_status=401):
        self.valid, self.bad_status, self.calls = set(valid), bad_status, []

    def post(self, url, params=None, headers=None, json=None, timeout=None):
        tok = params["access_token"]
        self.calls.append(tok)
        if tok in self.valid:
            return Resp(200, {"data": {"ok": True}})
        return Resp(self.bad_status, text='{"status":{"sub_code":"invalid_token"}}')


def tokens(access, refresh, secs=7200):
    return TokenSet(access, refresh, utcnow() + timedelta(seconds=secs))


def make(valid=(), *results, token="old-access", refresh="R1", expires_in=None, bad_status=401, with_refresher=True):
    refresher = ScriptedRefresher(*results) if with_refresher else None
    c = AiesecClient(token, "https://gql", delay=0, refresher=refresher, refresh_token=refresh, refresh_margin=600)
    c._http = GqlHttp(valid, bad_status)
    if expires_in is not None:
        c.expires_at = utcnow() + timedelta(seconds=expires_in)
    saved = []
    c.on_tokens = lambda cl: saved.append((cl.token, cl.refresh_token))
    return c, refresher, saved


def test_401_triggers_one_refresh_and_a_retry():
    c, rf, saved = make({"new-access"}, tokens("new-access", "R2"))
    assert c.gql("{x}") == {"ok": True}
    assert c._http.calls == ["old-access", "new-access"]
    assert rf.calls == ["R1"]
    assert c.refresh_token == "R2" and saved == [("new-access", "R2")]   # ротация сохранена
    assert c.auth_ok is True and c.token_source == "refresh"


def test_proactive_refresh_before_expiry_never_uses_old_token():
    c, rf, _ = make({"new-access"}, tokens("new-access", "R2"), expires_in=60)
    c.gql("{x}")
    assert c._http.calls == ["new-access"] and rf.calls == ["R1"]


def test_no_refresh_while_token_has_plenty_of_time():
    c, rf, _ = make({"old-access"}, expires_in=3600)
    c.gql("{x}")
    assert rf.calls == [] and c._http.calls == ["old-access"]


def test_unknown_expiry_is_not_refreshed_proactively():
    c, rf, _ = make({"old-access"})
    c.gql("{x}")
    assert rf.calls == []


def test_ensure_fresh_with_unknown_expiry_on_startup():
    c, rf, saved = make((), tokens("new-access", "R2"))
    c.ensure_fresh(refresh_if_unknown=True)
    assert c.token == "new-access" and 7000 < c.seconds_left() <= 7200 and saved


def test_only_refresh_token_given_gets_access_token_on_first_call():
    c, rf, _ = make({"new-access"}, tokens("new-access", "R2"), token="")
    c.gql("{x}")
    assert c._http.calls == ["new-access"]


def test_dead_refresh_token_fails_cleanly_without_looping():
    c, rf, _ = make((), AuthError("refresh_token отклонён (400)"))
    with pytest.raises(AuthError):
        c.gql("{x}")
    assert c.auth_ok is False and "отклонён" in c.auth_error
    assert rf.calls == ["R1"] and c._http.calls == ["old-access"]


def test_refreshed_token_also_rejected_stops_after_one_refresh():
    c, rf, _ = make((), tokens("new-access", "R2"))
    with pytest.raises(AuthError):
        c.gql("{x}")
    assert len(rf.calls) == 1 and c._http.calls == ["old-access", "new-access"] and c.auth_ok is False


def test_stale_401_does_not_burn_refresh_token_twice():
    c, rf, _ = make((), tokens("new-access", "R2"))
    c.refresh_after_401("old-access")
    c.refresh_after_401("old-access")     # второй поток опоздал: токен уже новый
    assert rf.calls == ["R1"]


def test_transient_failure_on_proactive_refresh_keeps_working_with_old_token():
    c, rf, _ = make({"old-access"}, AiesecError("auth down"), expires_in=60)
    assert c.gql("{x}") == {"ok": True}
    assert c._http.calls == ["old-access"] and c.auth_ok is True


def test_transient_failure_on_401_refresh_is_not_reported_as_auth_error():
    c, rf, _ = make((), AiesecError("auth down"))
    with pytest.raises(AiesecError) as e:
        c.gql("{x}")
    assert not isinstance(e.value, AuthError)


def test_403_means_no_rights_and_does_not_refresh():
    c, rf, _ = make((), bad_status=403)
    with pytest.raises(AuthError):
        c.gql("{x}")
    assert rf.calls == []


def test_without_refresher_behaves_as_before():
    c, _, _ = make((), with_refresher=False)
    assert not c.can_refresh
    with pytest.raises(AuthError):
        c.gql("{x}")


def test_failing_persistence_does_not_break_the_request():
    c, rf, _ = make({"new-access"}, tokens("new-access", "R2"))
    c.on_tokens = lambda cl: (_ for _ in ()).throw(RuntimeError("db down"))
    assert c.gql("{x}") == {"ok": True} and c.refresh_token == "R2"


def test_refresh_with_manual_token_applies_and_saves():
    c, rf, saved = make((), tokens("manual-access", "R9"))
    c.refresh_with("manual-R")
    assert rf.calls == ["manual-R"] and c.token == "manual-access" and saved == [("manual-access", "R9")]


def test_keeps_old_refresh_token_if_server_did_not_rotate():
    c, rf, _ = make((), TokenSet("new-access", None, utcnow() + timedelta(hours=2)))
    c.refresh_after_401("old-access")
    assert c.refresh_token == "R1"


def test_parallel_requests_share_a_single_refresh():
    """Планировщик и HTTP-ручка одновременно упёрлись в истёкший токен: refresh_token тратится один раз."""
    c, rf, _ = make({"new-access"}, tokens("new-access", "R2"), expires_in=60)
    errors = []

    def worker():
        try:
            c.gql("{x}")
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert errors == [] and rf.calls == ["R1"]


# ---------------- Settings ----------------



def S(**kw):
    base = dict(
        aiesec_token=None, aiesec_refresh_token=None,
        aiesec_client_id=None, aiesec_client_secret=None,
        allow_no_token=False,
    )
    return Settings(_env_file=None, **{**base, **kw})


def test_settings_need_some_credentials_or_explicit_allow():
    with pytest.raises(ValueError):
        S()


def test_allow_no_token_lets_settings_start_without_creds():
    s = S(allow_no_token=True)
    assert s.aiesec_token is None and not s.auto_refresh


def test_refresh_token_requires_client_credentials():
    with pytest.raises(ValueError):
        S(aiesec_refresh_token="r" * 12)


def test_refresh_only_setup_is_valid_and_enables_auto_refresh():
    s = S(aiesec_refresh_token="r" * 12, aiesec_client_id="id", aiesec_client_secret="sec")
    assert s.auto_refresh and s.aiesec_token is None


def test_blank_values_from_env_count_as_unset():
    s = S(aiesec_token="tok" * 5, aiesec_refresh_token="   ", aiesec_client_id="")
    assert s.aiesec_refresh_token is None and not s.auto_refresh