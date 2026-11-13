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


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    cl = request.headers.get("content-length")
    try:
        if cl is not None and int(cl) > get_settings().request_body_max_bytes:
            return JSONResponse({"detail": "request body too large"}, status_code=413)
    except ValueError:
        pass
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


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