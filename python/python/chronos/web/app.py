"""HTTP-Schicht (FastAPI): Operationsendpunkte, Beschreibung, KI-Werkzeuge, Anmeldung, Gesundheit, Statisches."""
import json
import os
import uuid
from contextlib import asynccontextmanager

from authlib.integrations.base_client import OAuthError
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from chronos import catalog, db  # noqa: F401  (catalog meldet alle Operationen an)
from chronos.config import settings
from chronos.core.errors import ChronosError, NotFound, Unauthenticated, ValidationFailed
from chronos.logging import correlation_id_var, log
from chronos.ops import executor
from chronos.ops.registry import OPERATIONS, describe, tool_definition
from chronos.web import auth


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.migrate()
    yield
    await db.engine().dispose()


app = FastAPI(title="Chronos Spike", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


class CorrelationMiddleware:
    """Setzt/übernimmt X-Correlation-Id (≤ 64 Zeichen), gibt sie zurück und protokolliert jede Anfrage."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.inner(scope, receive, send)
        incoming = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"x-correlation-id"), "")
        corr = incoming if 0 < len(incoming) <= 64 else str(uuid.uuid4())
        correlation_id_var.set(corr)
        status = 500

        async def send_wrapper(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message.setdefault("headers", [])
                message["headers"] = [h for h in message["headers"] if h[0].lower() != b"x-correlation-id"]
                message["headers"].append((b"x-correlation-id", corr.encode("latin-1")))
            await send(message)

        try:
            await self.inner(scope, receive, send_wrapper)
        finally:
            if scope["path"] != "/healthz":
                log.info("%s %s -> %s", scope["method"], scope["path"], status)


app.add_middleware(CorrelationMiddleware)


def _error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse({"error": {"code": code, "message": message}}, status_code=status)


@app.exception_handler(ChronosError)
async def _chronos_error(_: Request, e: ChronosError):
    return _error(e.status, e.code, e.message)


@app.exception_handler(RequestValidationError)
async def _validation_error(_: Request, e: RequestValidationError):
    return _error(422, "validation_error", str(e.errors()[0]["msg"]) if e.errors() else "ungültige Anfrage")


@app.exception_handler(StarletteHTTPException)
async def _http_error(_: Request, e: StarletteHTTPException):
    code = {401: "unauthenticated", 403: "forbidden", 404: "not_found"}.get(e.status_code, "internal")
    return _error(e.status_code, code, str(e.detail))


@app.exception_handler(Exception)
async def _unhandled(_: Request, e: Exception):
    log.error("unbehandelter Fehler: %s", e, exc_info=e)
    return _error(500, "internal", "interner Fehler")


@app.get("/healthz")
async def healthz():
    if await db.ping():
        return {"status": "ok"}
    return _error(503, "internal", "Datenbank nicht erreichbar")


# Beschreibung und Werkzeuge entstehen einmal aus der Registry (keine zweite Liste).
_DESCRIPTION: dict | None = None
_TOOLS: dict | None = None


@app.get("/api/v1/operations")
async def operations_description():
    global _DESCRIPTION
    if _DESCRIPTION is None:
        _DESCRIPTION = {"operations": [describe(op) for op in OPERATIONS.values()]}
    return _DESCRIPTION


@app.get("/api/v1/ai/tools")
async def ai_tools():
    global _TOOLS
    if _TOOLS is None:
        _TOOLS = {"tools": [tool_definition(op) for op in OPERATIONS.values()]}
    return _TOOLS


@app.post("/api/v1/operations/{name}")
async def call_operation(name: str, request: Request):
    op = OPERATIONS.get(name)
    if op is None:
        raise NotFound(f"Operation {name} unbekannt")
    person = await auth.authenticate(request)
    try:
        body = json.loads(await request.body() or b"{}")
    except ValueError as e:
        raise ValidationFailed("Anfrage ist kein gültiges JSON") from e
    if not isinstance(body, dict) or not isinstance(body.get("params", {}), dict) \
            or not isinstance(body.get("preview", False), bool) or set(body) - {"params", "preview"}:
        raise ValidationFailed('erwartet {"params":{…},"preview":false}')
    fault = request.headers.get("x-spike-fault")
    out = await executor.execute(op, body.get("params", {}), preview=body.get("preview", False), person=person,
                                 correlation_id=correlation_id_var.get() or "", fault=fault)
    return out


@app.get("/api/v1/push/vapid-public-key")
async def vapid_public_key():
    return {"public_key": settings.vapid_public_key}


# ---------------------------------------------------------------- Anmeldung (S-6)
@app.get("/auth/login")
async def login():
    return RedirectResponse(await auth.login_url(), status_code=302)


@app.get("/auth/callback")
async def callback(request: Request, code: str = "", state: str = ""):
    if not code or not state:
        return _error(400, "validation_error", "code und state erforderlich")
    try:
        sid = await auth.complete_login(code, state)
    except (OAuthError, Unauthenticated) as e:
        log.warning("Anmeldung fehlgeschlagen: %s", type(e).__name__)
        return _error(400, "validation_error", "Anmeldung fehlgeschlagen")
    if sid is None:
        return _error(400, "validation_error", "ungültiger state")
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(auth.COOKIE, sid, httponly=True, samesite="lax", path="/")
    return resp


@app.get("/auth/me")
async def me(request: Request):
    p = await auth.authenticate(request)
    return {"person_id": p.id, "name": p.name, "email": p.email}


@app.post("/auth/logout")
async def logout(request: Request):
    sid = request.cookies.get(auth.COOKIE)
    if sid:
        await auth.end_session(sid)
    resp = Response(status_code=204)
    resp.delete_cookie(auth.COOKIE, path="/")
    return resp


if os.path.isdir(settings.static_dir):
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
