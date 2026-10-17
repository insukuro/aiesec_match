from __future__ import annotations

import json


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