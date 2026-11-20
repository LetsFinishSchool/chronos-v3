"""Gemeinsame Hilfen der Abnahmesuite (nur Standardbibliothek)."""
import http.cookiejar
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------- Konfiguration
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080")
WORKER_HEALTH_URL = os.environ.get("WORKER_HEALTH_URL", "http://localhost:8081")
KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8180")
REALM = os.environ.get("KEYCLOAK_REALM", "chronos-spike")
TEST_CLIENT = os.environ.get("KEYCLOAK_TEST_CLIENT", "chronos-spike-test")
MAILPIT_URL = os.environ.get("MAILPIT_URL", "http://localhost:8025")
MOCK_URL = os.environ.get("MOCK_URL", "http://localhost:8090")
PASSWORD = os.environ.get("SPIKE_USER_PASSWORD", "spike-pass")
EMAIL_PRICE_MICRO_EUR = int(os.environ.get("EMAIL_PRICE_MICRO_EUR", "1000"))
RETRY_BASE_MS = int(os.environ.get("RETRY_BASE_MS", "200"))
# Docker-Compose-Aufruf zum Beenden/Starten des Workers und für Logs, z. B.
#   COMPOSE="docker compose -p chronos-spike-ts -f /pfad/compose.yaml"
COMPOSE = os.environ.get("COMPOSE", "")
CANDIDATE_DIR = os.environ.get("CANDIDATE_DIR", "")
SKIP_AI = os.environ.get("SKIP_AI") == "1"
HERE = os.path.dirname(os.path.abspath(__file__))

NOTES = {}  # Zusatzangaben für den Bericht (z. B. Duplikate), vom Runner ausgegeben


def note(key, value):
    NOTES[key] = value
    print(f"[Hinweis] {key}: {value}")


USERS = {"alice": "alice@example.test", "bob": "bob@example.test", "carol": "carol@example.test"}


# ---------------------------------------------------------------- HTTP
class Resp:
    def __init__(self, status, headers, body):
        self.status, self.headers, self.raw = status, headers, body
        try:
            self.json = json.loads(body) if body else None
        except ValueError:
            self.json = None

    def __repr__(self):
        return f"<Resp {self.status} {self.raw[:300]!r}>"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def http(method, url, *, headers=None, body=None, form=None, timeout=30, follow=False, opener=None):
    data = None
    headers = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        headers.setdefault("Content-Type", "application/json")
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers.setdefault("Content-Type", "application/x-www-form-urlencoded")
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    op = opener or (urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect))
    try:
        with op.open(req, timeout=timeout) as r:
            return Resp(r.status, r.headers, r.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return Resp(e.code, e.headers, e.read().decode("utf-8", "replace"))


def wait_for(fn, *, timeout=30.0, interval=0.25, what="Bedingung"):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        last = fn()
        if last:
            return last
        time.sleep(interval)
    raise AssertionError(f"Zeitüberschreitung ({timeout}s) beim Warten auf: {what}")


def uid(prefix=""):
    return prefix + uuid.uuid4().hex[:10]


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def future(days=30, hours=0):
    from datetime import timedelta
    return datetime.now(timezone.utc).replace(microsecond=0) + timedelta(days=days, hours=hours)


# ---------------------------------------------------------------- Keycloak
_tokens = {}


def token(user):
    t = _tokens.get(user)
    if t and t[1] > time.time() + 30:
        return t[0]
    r = http("POST", f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
             form={"grant_type": "password", "client_id": TEST_CLIENT, "username": user, "password": PASSWORD,
                   "scope": "openid email profile"})
    assert r.status == 200, f"Keycloak-Token für {user} nicht erhältlich: {r}"
    _tokens[user] = (r.json["access_token"], time.time() + r.json.get("expires_in", 60))
    return _tokens[user][0]


def subject(user):
    import base64
    payload = token(user).split(".")[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))["sub"]


# ---------------------------------------------------------------- API
class Api:
    def __init__(self, user):
        self.user = user

    @property
    def sub(self):
        return subject(self.user)

    def raw(self, method, path, *, body=None, headers=None, bearer=True):
        h = dict(headers or {})
        if bearer:
            h["Authorization"] = f"Bearer {token(self.user)}"
        return http(method, BASE_URL + path, headers=h, body=body)

    def op(self, name, params=None, *, preview=False, corr=None, headers=None, bearer=True):
        h = dict(headers or {})
        if corr:
            h["X-Correlation-Id"] = corr
        body = {"params": params or {}}
        if preview:
            body["preview"] = True
        return self.raw("POST", f"/api/v1/operations/{name}", body=body, headers=h, bearer=bearer)

    def ok(self, name, params=None, **kw):
        r = self.op(name, params, **kw)
        assert r.status == 200, f"{name} {params}: erwartet 200, war {r}"
        j = r.json
        return j["preview"] if kw.get("preview") and "preview" in j else j["result"]

    def err(self, name, params, status, code=None, **kw):
        r = self.op(name, params, **kw)
        assert r.status == status, f"{name}: erwartet {status}, war {r}"
        if code:
            assert r.json and r.json.get("error", {}).get("code") == code, f"{name}: Fehlercode erwartet {code}: {r}"
        return r


def alice(): return Api("alice")
def bob(): return Api("bob")
def carol(): return Api("carol")


def register_all():
    """Macht alle Testpersonen dem Dienst bekannt (erster authentifizierter Zugriff)."""
    for u in USERS:
        Api(u).ok("team.effective_teams")


def make_team(owner, name=None, parent=None):
    p = {"name": name or uid("team-")}
    if parent:
        p["parent_id"] = parent
    return owner.ok("team.create", p)["team_id"]


def make_appointment(api, team_id, *, title=None, corr=None, days=30, headers=None):
    s = future(days)
    return api.op("appointment.create", {"team_id": team_id, "title": title or uid("termin-"), "starts_at": iso(s),
                                         "ends_at": iso(s.replace(hour=(s.hour + 1) % 24)),
                                         "timezone": "Europe/Berlin"}, corr=corr, headers=headers)


# ---------------------------------------------------------------- Mock-Kanal, Mailpit
def mock(method, path, body=None):
    return http(method, MOCK_URL + path, body=body)


def mock_reset(fail_for=None, latency_ms=50):
    mock("POST", "/reset")
    r = mock("POST", "/control", {"fail_for": fail_for or [], "latency_ms": latency_ms})
    assert r.status in (200, 204), f"Mock-Kanal nicht erreichbar: {r}"


def mailpit_messages_to(address):
    r = http("GET", f"{MAILPIT_URL}/api/v1/search?query=" + urllib.parse.quote(f"to:{address}"))
    assert r.status == 200, f"Mailpit: {r}"
    return r.json.get("messages", [])


def mailpit_headers(message_id):
    r = http("GET", f"{MAILPIT_URL}/api/v1/message/{message_id}/headers")
    assert r.status == 200, f"Mailpit-Header: {r}"
    from email.header import decode_header, make_header
    # Bibliotheken kodieren Kopfzeilen unterschiedlich (RFC 2047): vor dem Vergleich dekodieren
    return {k: ["".join(str(make_header(decode_header(v))).split()) if v else v for v in vals]
            for k, vals in r.json.items()}


# ---------------------------------------------------------------- Compose
def compose(*args, check=True):
    if not COMPOSE:
        raise AssertionError("Umgebungsvariable COMPOSE ist nicht gesetzt (z. B. 'docker compose -p x -f y.yaml')")
    out = subprocess.run(COMPOSE.split() + list(args), capture_output=True, text=True)
    if check and out.returncode != 0:
        raise AssertionError(f"compose {' '.join(args)} fehlgeschlagen: {out.stderr}")
    return out.stdout


# ---------------------------------------------------------------- Mini-JSON-Schema-Prüfung
def schema_errors(schema, value, path="$"):
    """Prüft das Notwendige (type, required, properties, additionalProperties, enum, Längen, Grenzen, items)."""
    errs = []
    t = schema.get("type")
    types = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
    if t and not (isinstance(value, types[t]) and not (t in ("integer", "number") and isinstance(value, bool))):
        return [f"{path}: Typ {t} erwartet, war {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: nicht in enum")
    if t == "string":
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: zu kurz")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: zu lang")
    if t in ("integer", "number"):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{path}: unter Minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{path}: über Maximum")
    if t == "array" and "items" in schema:
        for i, v in enumerate(value):
            errs += schema_errors(schema["items"], v, f"{path}[{i}]")
    if t == "object":
        props = schema.get("properties", {})
        for r in schema.get("required", []):
            if r not in value:
                errs.append(f"{path}: Pflichtfeld {r} fehlt")
        for k, v in value.items():
            if k in props:
                errs += schema_errors(props[k], v, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unbekanntes Feld {k}")
    return errs


def parse_utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
