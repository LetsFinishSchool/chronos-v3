"""Einstieg: `python -m chronos web|worker` (ein Image, zwei Startarten)."""
import sys

from chronos import logging as chronos_logging


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"
    chronos_logging.setup()
    if mode == "web":
        import uvicorn

        from chronos.config import settings
        uvicorn.run("chronos.web.app:app", host="0.0.0.0", port=settings.port, log_config=None, access_log=False,
                    workers=1)
    elif mode == "worker":
        import asyncio

        from chronos.worker.main import run
        asyncio.run(run())
    else:
        raise SystemExit(f"unbekannte Startart {mode!r} (web|worker)")


main()
