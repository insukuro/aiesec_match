import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    auth, feedback, health, me, meta, notifications, opportunities,
    profiles, recommendations, subscriptions,
)
from .config import get_settings
from .errors import Problem, problem_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_settings().openapi_path.parent.mkdir(parents=True, exist_ok=True)
    yield
    get_settings().openapi_path.write_text(
        app.openapi_json() if hasattr(app, "openapi_json") else
        __import__("json").dumps(app.openapi(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


app = FastAPI(title="aiesec_match backend", version="1.0", lifespan=lifespan)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    body = await request.body()
    if len(body) > get_settings().request_body_max_bytes:
        return JSONResponse({"detail": "request body too large"}, status_code=413)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


app.add_exception_handler(Problem, problem_handler)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"], expose_headers=["X-Request-ID", "ETag"],
)

for module in (auth, me, meta, profiles, opportunities, recommendations,
               feedback, subscriptions, health):
    app.include_router(module.router, prefix="/api/v1")

app.include_router(notifications.router, prefix="/internal/v1")