from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from ..errors import Unauthorized


def verify_init_data(init_data: str, bot_token: str) -> dict:
    """Проверяет Telegram WebApp initData и возвращает user-объект."""
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = pairs.pop("hash", "")
    data_check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hashlib.sha256(bot_token.encode()).digest()
    expected = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(received_hash, expected):
        raise Unauthorized("bad initData signature")
    auth_date = int(pairs.get("auth_date", "0"))
    if datetime.now(timezone.utc).timestamp() - auth_date > 24 * 3600:
        raise Unauthorized("initData expired")
    return json.loads(pairs["user"])