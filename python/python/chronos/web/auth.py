"""Anmeldung: Token-Prüfung (PyJWT + JWKS) und OIDC-Code-Flow mit PKCE (Authlib). Kein Eigenbau-Kryptocode."""
import asyncio
import secrets
from typing import Any

import httpx
import jwt
from authlib.common.security import generate_token
from authlib.integrations.httpx_client import AsyncOAuth2Client
from fastapi import Request
from sqlalchemy import text

from chronos import db
from chronos.config import settings
from chronos.core.context import Person
from chronos.core.errors import Unauthenticated

COOKIE = "chronos_session"
_jwks = jwt.PyJWKClient(f"{settings.oidc_issuer_url}/protocol/openid-connect/certs", cache_keys=True, lifespan=300)
_discovery: dict[str, Any] | None = None


async def verify_token(token: str) -> dict[str, Any]:
    """Prüft Signatur (JWKS), iss und exp; gibt die Claims zurück."""
    try:
        key = await asyncio.to_thread(_jwks.get_signing_key_from_jwt, token)
        return jwt.decode(token, key.key, algorithms=["RS256"], issuer=settings.oidc_issuer_url,
                          options={"verify_aud": False, "require": ["exp", "iss", "sub"]})
    except (jwt.PyJWTError, ValueError) as e:
        raise Unauthenticated("Token ungültig") from e


async def upsert_person(claims: dict[str, Any]) -> Person:
    sub = claims["sub"]
    person = Person(id=sub, name=claims.get("preferred_username") or sub, email=claims.get("email") or "")
    async with db.session() as s, s.begin():
        await s.execute(
            text("INSERT INTO person (id, name, email) VALUES (:id, :name, :email) ON CONFLICT (id) DO UPDATE "
                 "SET name = EXCLUDED.name, email = EXCLUDED.email "
                 "WHERE person.name IS DISTINCT FROM EXCLUDED.name OR person.email IS DISTINCT FROM EXCLUDED.email"),
            {"id": person.id, "name": person.name, "email": person.email})
    return person


async def person_from_session(session_id: str) -> Person | None:
    async with db.session() as s:
        row = (await s.execute(text("SELECT person_id, name, email FROM session WHERE id = :id"),
                               {"id": session_id})).first()
    return Person(row.person_id, row.name, row.email) if row else None


async def authenticate(request: Request) -> Person:
    """Bearer-Token oder Sitzungscookie; sonst 401. Die Person wird beim ersten Zugriff angelegt/aktualisiert."""
    header = request.headers.get("authorization", "")
    if header:
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise Unauthenticated("Bearer-Token erwartet")
        return await upsert_person(await verify_token(token.strip()))
    cookie = request.cookies.get(COOKIE)
    if cookie and (person := await person_from_session(cookie)):
        return person
    raise Unauthenticated("Anmeldung erforderlich")


async def _endpoints() -> dict[str, Any]:
    global _discovery
    if _discovery is None:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{settings.oidc_issuer_url}/.well-known/openid-configuration")
            r.raise_for_status()
            _discovery = r.json()
    return _discovery


def _client() -> AsyncOAuth2Client:
    return AsyncOAuth2Client(client_id=settings.oidc_client_id, client_secret=settings.oidc_client_secret,
                             scope="openid email profile", redirect_uri=settings.oidc_redirect_url,
                             code_challenge_method="S256", timeout=10)


async def login_url() -> str:
    """Autorisierungs-URL (Code-Flow, PKCE S256, state); Verifier und state liegen serverseitig."""
    verifier = generate_token(64)
    async with _client() as client:
        url, state = client.create_authorization_url((await _endpoints())["authorization_endpoint"],
                                                     code_verifier=verifier)
    async with db.session() as s, s.begin():
        await s.execute(text("DELETE FROM oidc_login WHERE created_at < now() - interval '10 minutes'"))
        await s.execute(text("INSERT INTO oidc_login (state, verifier) VALUES (:s, :v)"), {"s": state, "v": verifier})
    return url


async def complete_login(code: str, state: str) -> str | None:
    """Tauscht den Code; gibt die neue Sitzungs-ID zurück oder None bei ungültigem state."""
    async with db.session() as s, s.begin():
        verifier = (await s.execute(
            text("DELETE FROM oidc_login WHERE state = :s AND created_at > now() - interval '10 minutes' "
                 "RETURNING verifier"), {"s": state})).scalar_one_or_none()
    if verifier is None:
        return None
    async with _client() as client:
        token = await client.fetch_token((await _endpoints())["token_endpoint"], code=code, code_verifier=verifier,
                                         grant_type="authorization_code")
    claims = await verify_token(token.get("id_token") or token["access_token"])
    person = await upsert_person(claims)
    sid = secrets.token_urlsafe(32)
    async with db.session() as s, s.begin():
        await s.execute(text("INSERT INTO session (id, person_id, name, email) VALUES (:id, :p, :n, :e)"),
                        {"id": sid, "p": person.id, "n": person.name, "e": person.email})
    return sid


async def end_session(session_id: str) -> None:
    async with db.session() as s, s.begin():
        await s.execute(text("DELETE FROM session WHERE id = :id"), {"id": session_id})
