"""Worker: Gesundheitsendpunkt (uvicorn) plus Zustellschleife."""
import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from chronos import db
from chronos.config import settings
from chronos.logging import log
from chronos.worker import delivery


@asynccontextmanager
async def lifespan(_: FastAPI):
    await db.wait_for_schema(60)
    log.info("Worker gestartet")
    task = asyncio.create_task(delivery.run_loop())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/healthz")
async def healthz():
    if await db.ping():
        return {"status": "ok"}
    return JSONResponse({"error": {"code": "internal", "message": "Datenbank nicht erreichbar"}}, status_code=503)


async def run() -> None:
    cfg = uvicorn.Config(app, host="0.0.0.0", port=settings.worker_health_port, log_config=None, access_log=False)
    await uvicorn.Server(cfg).serve()
