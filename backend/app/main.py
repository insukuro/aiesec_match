import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    analytics, auth, feedback, health, history, me, meta, notifications,
    opportunities, profiles, recommendations, subscriptions,
)
from .config import get_settings
from .errors import Problem, problem_handler
from starlette.types import ASGIApp, Scope, Receive, Send

@asynccontextmanager
async def lifespan(app: FastAPI):
    from .matcher_client import MatcherClient
    app.state.matcher = MatcherClient()
    get_settings().openapi_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        yield
    finally:
        await app.state.matcher.aclose()
        get_settings().openapi_path.write_text(
            json.dumps(app.openapi(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


app = FastAPI(title="aiesec_match backend", version="1.2", lifespan=lifespan)


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        rid = (headers.get(b"x-request-id") or b"").decode() or str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = rid

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                message.setdefault("headers", []).append(
                    (b"x-request-id", rid.encode())
                )
            await send(message)

        await self.app(scope, receive, send_wrapper)


app.add_middleware(RequestContextMiddleware)

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = []
    for e in exc.errors():
        loc = list(e.get("loc", []))
        msg = e.get("msg") or "invalid"
        # pydantic оборачивает наш ValueError в "Value error, <msg>"
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        errors.append({"loc": loc, "msg": msg})
    return JSONResponse(
        {
            "type": "/problems/validation",
            "title": "Validation error",
            "status": 422,
            "detail": "",
            "instance": request.url.path,
            "request_id": getattr(request.state, "request_id", None),
            "errors": errors,
        },
        status_code=422,
        media_type="application/problem+json",
    )


app.add_exception_handler(Problem, problem_handler)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Request-ID", "ETag"],
)

for module in (auth, me, meta, profiles, opportunities, recommendations,
               feedback, subscriptions, analytics, history, health):
    app.include_router(module.router, prefix="/api/v1")

app.include_router(notifications.router, prefix="/internal/v1")