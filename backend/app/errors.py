from fastapi import Request, status
from fastapi.responses import JSONResponse


class Problem(Exception):
    type: str = "about:blank"
    title: str = "Error"
    status_code: int = 400

    def __init__(self, detail: str = "", errors: list[dict] | None = None):
        self.detail = detail
        self.errors = errors or []


class Validation(Problem):     type = "/problems/validation";        title = "Validation error";       status_code = 422
class Unauthorized(Problem):   type = "/problems/unauthorized";      title = "Unauthorized";           status_code = 401
class ConsentRequired(Problem):type = "/problems/consent-required";  title = "Consent required";       status_code = 403
class ProfileNotFound(Problem):type = "/problems/profile-not-found"; title = "Profile not found";      status_code = 404
class OpportunityNotFound(Problem): type = "/problems/opportunity-not-found"; title = "Opportunity not found"; status_code = 404
class RunNotFound(Problem):    type = "/problems/run-not-found";     title = "Run not found";          status_code = 404
class ProfileIncomplete(Problem): type = "/problems/profile-incomplete"; title = "Profile incomplete"; status_code = 409
class VersionConflict(Problem):type = "/problems/version-conflict";  title = "Version conflict";       status_code = 412
class RateLimited(Problem):    type = "/problems/rate-limited";      title = "Rate limited";           status_code = 429
class MatcherUnavailable(Problem): type = "/problems/matcher-unavailable"; title = "Matcher unavailable"; status_code = 503
class MatcherTimeout(Problem): type = "/problems/matcher-timeout";   title = "Matcher timeout";        status_code = 504
class InvalidLinkCode(Problem):type = "/problems/invalid-link-code"; title = "Invalid link code";      status_code = 404
class LinkCodeExpired(Problem):type = "/problems/link-code-expired"; title = "Link code expired";      status_code = 410


async def problem_handler(request: Request, exc: Problem) -> JSONResponse:
    body = {
        "type": exc.type,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": request.url.path,
        "request_id": getattr(request.state, "request_id", None),
        "errors": exc.errors,
    }
    headers = {}
    if exc.status_code == 429 and hasattr(exc, "retry_after"):
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(body, status_code=exc.status_code,
                        media_type="application/problem+json", headers=headers)