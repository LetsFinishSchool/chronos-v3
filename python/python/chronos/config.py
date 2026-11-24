"""Konfiguration aus Umgebungsvariablen (V-1 §2)."""
import os
from dataclasses import dataclass


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


@dataclass(frozen=True)
class Settings:
    database_url: str
    port: int
    worker_health_port: int
    oidc_issuer_url: str
    oidc_client_id: str
    oidc_client_secret: str
    oidc_redirect_url: str
    smtp_host: str
    smtp_port: int
    vapid_public_key: str
    vapid_private_key: str
    vapid_subject: str
    mock_channel_url: str
    anthropic_base_url: str | None
    anthropic_api_key: str
    anthropic_model: str
    ai_price_in: int
    ai_price_out: int
    email_price: int
    retry_base_ms: int
    static_dir: str
    spike_faults: bool


def load() -> Settings:
    e = os.environ
    url = e.get("DATABASE_URL", "postgres://chronos:chronos@localhost:5432/chronos")
    # SQLAlchemy braucht den Treibernamen: postgres(ql):// -> postgresql+psycopg://
    url = "postgresql+psycopg://" + url.split("://", 1)[1]
    return Settings(
        database_url=url,
        port=_int("PORT", 8080),
        worker_health_port=_int("WORKER_HEALTH_PORT", 8081),
        oidc_issuer_url=e.get("OIDC_ISSUER_URL", "").rstrip("/"),
        oidc_client_id=e.get("OIDC_CLIENT_ID", ""),
        oidc_client_secret=e.get("OIDC_CLIENT_SECRET", ""),
        oidc_redirect_url=e.get("OIDC_REDIRECT_URL", ""),
        smtp_host=e.get("SMTP_HOST", "localhost"),
        smtp_port=_int("SMTP_PORT", 1025),
        vapid_public_key=e.get("VAPID_PUBLIC_KEY", ""),
        vapid_private_key=e.get("VAPID_PRIVATE_KEY", ""),
        vapid_subject=e.get("VAPID_SUBJECT", "mailto:spike@example.test"),
        mock_channel_url=e.get("MOCK_CHANNEL_URL", "http://localhost:8090").rstrip("/"),
        anthropic_base_url=e.get("ANTHROPIC_BASE_URL") or None,
        anthropic_api_key=e.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=e.get("ANTHROPIC_MODEL", "claude-haiku-5-5"),
        ai_price_in=_int("AI_PRICE_IN_MICRO_EUR_PER_MTOK", 0),
        ai_price_out=_int("AI_PRICE_OUT_MICRO_EUR_PER_MTOK", 0),
        email_price=_int("EMAIL_PRICE_MICRO_EUR", 0),
        retry_base_ms=_int("RETRY_BASE_MS", 1000),
        static_dir=e.get("STATIC_DIR", "/static"),
        spike_faults=e.get("SPIKE_FAULTS") == "1",
    )


settings = load()
