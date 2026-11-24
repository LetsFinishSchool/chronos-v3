"""Referenzattrappe zu V-1 (Spike E-002). KEIN Kandidat: dient nur der Validierung der Abnahmesuite (V-2).

Eine Datei, zwei Startarten:  ref_server.py web | worker
Zustand liegt in PostgreSQL; Web und Worker teilen sich nur die Datenbank (ADR-002).
"""
import base64
import hashlib
import json
import os
import re
import secrets
import smtplib
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

import jwt
import psycopg
from dateutil import rrule as rr
from jwt import PyJWKClient
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

ENV = os.environ.get
DATABASE_URL = ENV("DATABASE_URL")
ISSUER = ENV("OIDC_ISSUER_URL", "")
RETRY_BASE = int(ENV("RETRY_BASE_MS", "1000")) / 1000
FAULTS = ENV("SPIKE_FAULTS") == "1"
LOCAL = threading.local()


# ------------------------------------------------------------------ Logging
def log(level, msg, **kw):
    rec = {"ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"), "level": level, "msg": msg,
           "correlation_id": getattr(LOCAL, "corr", None)}
    rec.update(kw)
    print(json.dumps(rec, ensure_ascii=False), flush=True)


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


class InjectedFault(Exception):
    pass


def ts(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_utc(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


# ------------------------------------------------------------------ Datenbank
def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


SCHEMA = """
CREATE TABLE IF NOT EXISTS persons(sub text PRIMARY KEY, name text, email text, channels text[] NOT NULL DEFAULT '{webpush,email}');
CREATE TABLE IF NOT EXISTS push_subs(id serial PRIMARY KEY, person text, endpoint text, p256dh text, auth text);
CREATE TABLE IF NOT EXISTS teams(id uuid PRIMARY KEY, name text, parent_id uuid);
CREATE TABLE IF NOT EXISTS members(team_id uuid, person text, PRIMARY KEY(team_id, person));
CREATE TABLE IF NOT EXISTS appts(id uuid PRIMARY KEY, team_id uuid, title text, starts_at timestamptz, ends_at timestamptz, tz text, status text);
CREATE TABLE IF NOT EXISTS series(id uuid PRIMARY KEY, team_id uuid, title text, rrule text, dtstart text, tz text, duration int, exdates jsonb);
CREATE TABLE IF NOT EXISTS history(id uuid PRIMARY KEY, seq bigserial, at timestamptz, actor text, action text, object_type text,
  object_id uuid, team_id uuid, before jsonb, after jsonb, bundle_id uuid, corr text, undone boolean NOT NULL DEFAULT false, undo_of uuid);
CREATE TABLE IF NOT EXISTS events(id uuid PRIMARY KEY, type text, trigger jsonb, corr text, created timestamptz);
CREATE TABLE IF NOT EXISTS tasks(id bigserial PRIMARY KEY, event_id uuid, recipient text, forced text, state text NOT NULL DEFAULT 'pending');
CREATE TABLE IF NOT EXISTS deliveries(id bigserial PRIMARY KEY, event_id uuid, event_type text, corr text, trigger jsonb, actor text,
  recipient text, channel text, attempt int, result text, error text, at timestamptz, key text);
CREATE TABLE IF NOT EXISTS costs(id uuid PRIMARY KEY, at timestamptz, person text, provider text, trigger jsonb, quantity jsonb, amount bigint);
CREATE TABLE IF NOT EXISTS sessions(id text PRIMARY KEY, person text);
CREATE TABLE IF NOT EXISTS auth_flows(state text PRIMARY KEY, verifier text);
"""


def migrate():
    for attempt in range(60):
        try:
            with connect() as c:
                c.execute("SELECT pg_advisory_xact_lock(4711)")
                c.execute(SCHEMA)
            return
        except psycopg.OperationalError:
            time.sleep(1)
    raise SystemExit("Datenbank nicht erreichbar")


# ------------------------------------------------------------------ Schema-Helfer (eine Beschreibung für alles)
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
LOCAL_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")


def obj(props, required=None):
    return {"type": "object", "properties": props, "required": required if required is not None else list(props),
            "additionalProperties": False}


def res_obj(props):
    return {"type": "object", "properties": props, "required": list(props)}


STR = {"type": "string"}
UUID = {"type": "string", "format": "uuid"}
UTCT = {"type": "string", "format": "date-time"}
TZ = {"type": "string", "format": "iana-timezone"}


def s_str(lo=1, hi=None):
    d = {"type": "string", "minLength": lo}
    if hi:
        d["maxLength"] = hi
    return d


def validate(schema, v, path="params"):
    t = schema.get("type")
    py = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}
    if t and (not isinstance(v, py[t]) or (t in ("integer", "number") and isinstance(v, bool))):
        raise ApiError(422, "validation_error", f"{path}: Typ {t} erwartet")
    if t == "string":
        if len(v) < schema.get("minLength", 0) or len(v) > schema.get("maxLength", 10 ** 9):
            raise ApiError(422, "validation_error", f"{path}: Länge")
        f = schema.get("format")
        if f == "uuid" and not UUID_RE.match(v):
            raise ApiError(422, "validation_error", f"{path}: keine UUID")
        if f == "date-time" and not UTC_RE.match(v):
            raise ApiError(422, "validation_error", f"{path}: UTC-Zeitpunkt erwartet")
        if f == "local-date-time" and not LOCAL_RE.match(v):
            raise ApiError(422, "validation_error", f"{path}: Ortszeit erwartet")
        if f == "iana-timezone":
            try:
                ZoneInfo(v)
            except Exception:
                raise ApiError(422, "validation_error", f"{path}: unbekannte Zeitzone")
        if f == "https-url" and not v.startswith("https://"):
            raise ApiError(422, "validation_error", f"{path}: https-URL erwartet")
    if t in ("integer", "number"):
        if v < schema.get("minimum", -10 ** 18) or v > schema.get("maximum", 10 ** 18):
            raise ApiError(422, "validation_error", f"{path}: Wertebereich")
    if "enum" in schema and v not in schema["enum"]:
        raise ApiError(422, "validation_error", f"{path}: nicht erlaubt")
    if t == "array":
        if len(v) < schema.get("minItems", 0):
            raise ApiError(422, "validation_error", f"{path}: zu wenige Einträge")
        for i, x in enumerate(v):
            validate(schema["items"], x, f"{path}[{i}]")
    if t == "object":
        props = schema.get("properties", {})
        for r in schema.get("required", []):
            if r not in v:
                raise ApiError(422, "validation_error", f"{path}.{r}: fehlt")
        for k, x in v.items():
            if k in props:
                validate(props[k], x, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                raise ApiError(422, "validation_error", f"{path}.{k}: unbekannt")


# ------------------------------------------------------------------ Kontext und Fachhelfer
class Ctx:
    def __init__(self, conn, person, corr, preview, fault):
        self.conn, self.person, self.corr, self.preview, self.fault = conn, person, corr, preview, fault
        self.operation = None
        self.bundle = str(uuid.uuid4())


def q(conn, sql, *a):
    return conn.execute(sql, a).fetchall()


def q1(conn, sql, *a):
    return conn.execute(sql, a).fetchone()


EFF_MEMBERS = """WITH RECURSIVE d AS (SELECT id FROM teams WHERE id=%s UNION SELECT t.id FROM teams t JOIN d ON t.parent_id=d.id)
SELECT DISTINCT p.sub AS person_id, p.name FROM members m JOIN persons p ON p.sub=m.person
WHERE m.team_id IN (SELECT id FROM d) ORDER BY p.sub"""
EFF_TEAMS = """WITH RECURSIVE up AS (SELECT t.id, t.name, t.parent_id FROM teams t JOIN members m ON m.team_id=t.id WHERE m.person=%s
UNION SELECT t.id, t.name, t.parent_id FROM teams t JOIN up ON t.id=up.parent_id)
SELECT DISTINCT id::text AS team_id, name, parent_id::text AS parent_id FROM up ORDER BY name, team_id"""


def team_or_404(c, team_id):
    t = q1(c.conn, "SELECT * FROM teams WHERE id=%s", team_id)
    if not t:
        raise ApiError(404, "not_found", "Team nicht gefunden")
    return t


def require_member(c, team_id):
    team_or_404(c, team_id)
    if c.person["sub"] not in [m["person_id"] for m in q(c.conn, EFF_MEMBERS, team_id)]:
        raise ApiError(403, "forbidden", "kein Mitglied")


def appt_snapshot(r):
    return {"id": str(r["id"]), "team_id": str(r["team_id"]), "title": r["title"], "starts_at": ts(r["starts_at"]),
            "ends_at": ts(r["ends_at"]), "timezone": r["tz"], "status": r["status"]}


def appt_or_404(c, appt_id, with_deleted=False):
    r = q1(c.conn, "SELECT * FROM appts WHERE id=%s", appt_id)
    if not r or (r["status"] == "gelöscht" and not with_deleted):
        raise ApiError(404, "not_found", "Termin nicht gefunden")
    return r


def write_history(c, action, otype, oid, team_id, before, after, undo_of=None):
    hid = str(uuid.uuid4())
    c.conn.execute("INSERT INTO history(id, at, actor, action, object_type, object_id, team_id, before, after, bundle_id, corr, undo_of)"
                   " VALUES (%s, now(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                   (hid, c.person["sub"], action, otype, oid, team_id, Jsonb(before) if before is not None else None,
                    Jsonb(after) if after is not None else None, c.bundle, c.corr, undo_of))
    return hid


def emit(c, etype, recipients, forced=None):
    eid = str(uuid.uuid4())
    trig = {"kind": "person", "actor": c.person["sub"], "operation": c.operation}
    c.conn.execute("INSERT INTO events(id, type, trigger, corr, created) VALUES (%s, %s, %s, %s, now())",
                   (eid, etype, Jsonb(trig), c.corr))
    for r in recipients:
        c.conn.execute("INSERT INTO tasks(event_id, recipient, forced) VALUES (%s, %s, %s)", (eid, r, forced))
    log("info", "Ereignis festgehalten", event_id=eid, type=etype, recipients=len(recipients))
    return eid


def others(c, team_id):
    return [m["person_id"] for m in q(c.conn, EFF_MEMBERS, team_id) if m["person_id"] != c.person["sub"]]


# ------------------------------------------------------------------ Operationen (einmal beschrieben)
OPS = {}


def operation(name, desc, mutating, params, result, preview=False):
    def deco(fn):
        OPS[name] = {"name": name, "description": desc, "mutating": mutating, "preview_supported": preview,
                     "params_schema": params, "result_schema": result, "fn": fn}
        return fn
    return deco


@operation("team.create", "Team anlegen (optional unter einem Eltern-Team).", True,
           obj({"name": s_str(1, 100), "parent_id": UUID}, ["name"]), res_obj({"team_id": UUID}))
def team_create(c, p):
    if p.get("parent_id"):
        require_member(c, p["parent_id"])
    tid = str(uuid.uuid4())
    c.conn.execute("INSERT INTO teams(id, name, parent_id) VALUES (%s, %s, %s)", (tid, p["name"], p.get("parent_id")))
    c.conn.execute("INSERT INTO members(team_id, person) VALUES (%s, %s)", (tid, c.person["sub"]))
    return {"team_id": tid}


@operation("team.add_member", "Person zu einem Team hinzufügen.", True,
           obj({"team_id": UUID, "person_id": STR}), res_obj({}))
def team_add_member(c, p):
    require_member(c, p["team_id"])
    if not q1(c.conn, "SELECT 1 FROM persons WHERE sub=%s", p["person_id"]):
        raise ApiError(404, "not_found", "Person unbekannt")
    c.conn.execute("INSERT INTO members(team_id, person) VALUES (%s, %s) ON CONFLICT DO NOTHING", (p["team_id"], p["person_id"]))
    return {}


@operation("team.effective_members", "Alle Mitglieder eines Teams und seiner Unter-Teams.", False,
           obj({"team_id": UUID}),
           res_obj({"members": {"type": "array", "items": res_obj({"person_id": STR, "name": STR})}}))
def team_effective_members(c, p):
    require_member(c, p["team_id"])
    return {"members": [dict(m) for m in q(c.conn, EFF_MEMBERS, p["team_id"])]}


@operation("team.effective_teams", "Teams, in denen die Person (direkt oder über Unter-Teams) Mitglied ist.", False,
           obj({"person_id": STR}, []),
           res_obj({"teams": {"type": "array", "items": res_obj({"team_id": UUID, "name": STR, "parent_id": STR})}}))
def team_effective_teams(c, p):
    who = p.get("person_id", c.person["sub"])
    if who != c.person["sub"]:
        raise ApiError(403, "forbidden", "nur für die eigene Person")
    return {"teams": [dict(t) for t in q(c.conn, EFF_TEAMS, who)]}


APPT_SCHEMA = res_obj({"id": UUID, "team_id": UUID, "title": STR, "starts_at": UTCT, "ends_at": UTCT, "timezone": TZ,
                       "status": {"type": "string", "enum": ["geplant", "abgesagt", "gelöscht"]}})


@operation("appointment.create", "Termin in einem Team anlegen; benachrichtigt alle anderen Mitglieder.", True,
           obj({"team_id": UUID, "title": s_str(1, 200), "starts_at": UTCT, "ends_at": UTCT, "timezone": TZ}),
           res_obj({"appointment_id": UUID}))
def appointment_create(c, p):
    require_member(c, p["team_id"])
    if parse_utc(p["ends_at"]) <= parse_utc(p["starts_at"]):
        raise ApiError(422, "validation_error", "ends_at muss nach starts_at liegen")
    aid = str(uuid.uuid4())
    c.conn.execute("INSERT INTO appts VALUES (%s, %s, %s, %s, %s, %s, 'geplant')",
                   (aid, p["team_id"], p["title"], p["starts_at"], p["ends_at"], p["timezone"]))
    after = appt_snapshot(appt_or_404(c, aid))
    write_history(c, "appointment.create", "appointment", aid, p["team_id"], None, after)
    if FAULTS and c.fault == "after_history":
        raise InjectedFault("Fehlerinjektion nach dem Verlauf")
    emit(c, "appointment.created", others(c, p["team_id"]))
    return {"appointment_id": aid}


@operation("appointment.get", "Termin lesen.", False, obj({"appointment_id": UUID}), res_obj({"appointment": APPT_SCHEMA}))
def appointment_get(c, p):
    r = appt_or_404(c, p["appointment_id"])
    require_member(c, r["team_id"])
    return {"appointment": appt_snapshot(r)}


@operation("appointment.list", "Termine eines Teams lesen.", False, obj({"team_id": UUID}),
           res_obj({"appointments": {"type": "array", "items": APPT_SCHEMA}}))
def appointment_list(c, p):
    require_member(c, p["team_id"])
    rows = q(c.conn, "SELECT * FROM appts WHERE team_id=%s AND status<>'gelöscht' ORDER BY starts_at, id", p["team_id"])
    return {"appointments": [appt_snapshot(r) for r in rows]}


def preview_of(c, r, change):
    return {"count": 1, "affected": [{"type": "appointment", "id": str(r["id"]), "change": change}]}


@operation("appointment.cancel", "Termin absagen.", True, obj({"appointment_id": UUID}), res_obj({}), preview=True)
def appointment_cancel(c, p):
    r = appt_or_404(c, p["appointment_id"])
    require_member(c, r["team_id"])
    if r["status"] != "geplant":
        raise ApiError(409, "conflict", "Termin ist nicht geplant")
    if c.preview:
        return preview_of(c, r, "status: geplant -> abgesagt")
    before = appt_snapshot(r)
    c.conn.execute("UPDATE appts SET status='abgesagt' WHERE id=%s", (r["id"],))
    write_history(c, "appointment.cancel", "appointment", r["id"], r["team_id"], before, appt_snapshot(appt_or_404(c, r["id"])))
    emit(c, "appointment.cancelled", others(c, r["team_id"]))
    return {}


@operation("appointment.reschedule", "Termin verschieben.", True,
           obj({"appointment_id": UUID, "starts_at": UTCT, "ends_at": UTCT}), res_obj({}), preview=True)
def appointment_reschedule(c, p):
    r = appt_or_404(c, p["appointment_id"])
    require_member(c, r["team_id"])
    if parse_utc(p["ends_at"]) <= parse_utc(p["starts_at"]):
        raise ApiError(422, "validation_error", "ends_at muss nach starts_at liegen")
    if c.preview:
        return preview_of(c, r, f"Beginn: {ts(r['starts_at'])} -> {p['starts_at']}")
    before = appt_snapshot(r)
    c.conn.execute("UPDATE appts SET starts_at=%s, ends_at=%s WHERE id=%s", (p["starts_at"], p["ends_at"], r["id"]))
    write_history(c, "appointment.reschedule", "appointment", r["id"], r["team_id"], before, appt_snapshot(appt_or_404(c, r["id"])))
    emit(c, "appointment.rescheduled", others(c, r["team_id"]))
    return {}


HIST_ENTRY = res_obj({"id": UUID, "at": UTCT, "actor": STR, "action": STR, "object_type": STR, "object_id": UUID,
                      "before": {}, "after": {}, "bundle_id": UUID, "correlation_id": STR, "undone": {"type": "boolean"},
                      "undo_of": {}})


def hist_row(r):
    return {"id": str(r["id"]), "at": ts(r["at"]), "actor": r["actor"], "action": r["action"], "object_type": r["object_type"],
            "object_id": str(r["object_id"]), "before": r["before"], "after": r["after"], "bundle_id": str(r["bundle_id"]),
            "correlation_id": r["corr"], "undone": r["undone"], "undo_of": str(r["undo_of"]) if r["undo_of"] else None}


@operation("history.list", "Änderungsverlauf lesen (neueste zuerst).", False,
           obj({"object_id": UUID, "limit": {"type": "integer", "minimum": 1, "maximum": 200}}, []),
           res_obj({"entries": {"type": "array", "items": HIST_ENTRY}}))
def history_list(c, p):
    teams = [t["team_id"] for t in q(c.conn, EFF_TEAMS, c.person["sub"])]
    if not teams:
        return {"entries": []}
    sql = "SELECT * FROM history WHERE team_id::text = ANY(%s)"
    args = [teams]
    if p.get("object_id"):
        sql += " AND object_id=%s"
        args.append(p["object_id"])
    sql += " ORDER BY seq DESC LIMIT %s"
    args.append(p.get("limit", 50))
    return {"entries": [hist_row(r) for r in c.conn.execute(sql, args).fetchall()]}


@operation("history.undo", "Eine Änderung rückgängig machen.", True, obj({"history_id": UUID}), res_obj({"history_id": UUID}),
           preview=True)
def history_undo(c, p):
    e = q1(c.conn, "SELECT * FROM history WHERE id=%s", p["history_id"])
    if not e:
        raise ApiError(404, "not_found", "Verlaufseintrag nicht gefunden")
    require_member(c, e["team_id"])
    if e["object_type"] != "appointment":
        raise ApiError(409, "not_undoable", "nur Termine sind rückgängig machbar")
    cur = appt_snapshot(appt_or_404(c, e["object_id"], with_deleted=True))
    if cur != e["after"]:
        raise ApiError(409, "not_undoable", "Zustand des Objekts hat sich seit dem Eintrag geändert")
    target = e["before"] if e["before"] is not None else {**e["after"], "status": "gelöscht"}
    if c.preview:
        return {"count": 1, "affected": [{"type": "appointment", "id": str(e["object_id"]), "change": f"status: {cur['status']} -> {target['status']}"}]}
    c.conn.execute("UPDATE appts SET title=%s, starts_at=%s, ends_at=%s, tz=%s, status=%s WHERE id=%s",
                   (target["title"], target["starts_at"], target["ends_at"], target["timezone"], target["status"], e["object_id"]))
    c.conn.execute("UPDATE history SET undone=true WHERE id=%s", (e["id"],))
    hid = write_history(c, "history.undo", "appointment", e["object_id"], e["team_id"], cur, target, undo_of=e["id"])
    orig = [r["recipient"] for r in q(c.conn, "SELECT t.recipient FROM tasks t JOIN events ev ON ev.id=t.event_id WHERE ev.corr=%s", e["corr"])]
    emit(c, "change.reverted", [x for x in dict.fromkeys(orig)])
    return {"history_id": hid}


def validate_rrule(rule):
    if not rule or not re.match(r"^[A-Z]+=[^;]+(;[A-Z]+=[^;]+)*$", rule):
        raise ApiError(422, "invalid_rrule", "RRULE syntaktisch ungültig")
    parts = dict(x.split("=", 1) for x in rule.split(";"))
    if "FREQ" not in parts:
        raise ApiError(422, "invalid_rrule", "FREQ fehlt")
    if "COUNT" in parts and "UNTIL" in parts:
        raise ApiError(422, "invalid_rrule", "COUNT und UNTIL schließen sich aus")
    if "INTERVAL" in parts and (not parts["INTERVAL"].isdigit() or int(parts["INTERVAL"]) < 1):
        raise ApiError(422, "invalid_rrule", "INTERVAL muss ≥ 1 sein")
    for d in parts.get("BYMONTHDAY", "").split(","):
        if d and (int(d) == 0 or abs(int(d)) > 31):
            raise ApiError(422, "invalid_rrule", "BYMONTHDAY ungültig")
    try:
        rr.rrulestr(rule, dtstart=datetime(2026, 1, 1, tzinfo=timezone.utc))
    except Exception as ex:
        raise ApiError(422, "invalid_rrule", f"RRULE ungültig: {ex}")


@operation("series.create", "Serientermin (RRULE) anlegen.", True,
           obj({"team_id": UUID, "title": s_str(1, 200), "rrule": s_str(1), "dtstart": {"type": "string", "format": "local-date-time"},
                "timezone": TZ, "duration_minutes": {"type": "integer", "minimum": 1, "maximum": 1440},
                "exdates": {"type": "array", "items": {"type": "string", "format": "local-date-time"}}},
               ["team_id", "title", "rrule", "dtstart", "timezone", "duration_minutes"]),
           res_obj({"series_id": UUID}))
def series_create(c, p):
    require_member(c, p["team_id"])
    validate_rrule(p["rrule"])
    sid = str(uuid.uuid4())
    c.conn.execute("INSERT INTO series VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                   (sid, p["team_id"], p["title"], p["rrule"], p["dtstart"], p["timezone"], p["duration_minutes"],
                    Jsonb(p.get("exdates", []))))
    write_history(c, "series.create", "series", sid, p["team_id"], None, {"id": sid, "rrule": p["rrule"]})
    return {"series_id": sid}


@operation("series.occurrences", "Vorkommen einer Serie im Zeitraum berechnen.", False,
           obj({"series_id": UUID, "from": UTCT, "to": UTCT}),
           res_obj({"occurrences": {"type": "array", "items": res_obj({"starts_at": UTCT, "ends_at": UTCT})}}))
def series_occurrences(c, p):
    s = q1(c.conn, "SELECT * FROM series WHERE id=%s", p["series_id"])
    if not s:
        raise ApiError(404, "not_found", "Serie nicht gefunden")
    require_member(c, s["team_id"])
    tz = ZoneInfo(s["tz"])
    start = datetime.fromisoformat(s["dtstart"]).replace(tzinfo=tz)
    frm, to = parse_utc(p["from"]), parse_utc(p["to"])
    ex = {datetime.fromisoformat(e).replace(tzinfo=tz) for e in s["exdates"]}
    out = []
    for occ in rr.rrulestr(s["rrule"], dtstart=start):
        u = occ.astimezone(timezone.utc)
        if u >= to or len(out) >= 1000:
            break
        if occ in ex or u < frm:
            continue
        out.append({"starts_at": ts(u), "ends_at": ts(u + timedelta(minutes=s["duration"]))})
    return {"occurrences": out}


CHANNELS = ["mock", "email", "webpush"]


@operation("notification.set_channels", "Eigene Kanäle in Reihenfolge festlegen.", True,
           obj({"channels": {"type": "array", "minItems": 1, "items": {"type": "string", "enum": CHANNELS}}}), res_obj({}))
def set_channels(c, p):
    c.conn.execute("UPDATE persons SET channels=%s WHERE sub=%s", (p["channels"], c.person["sub"]))
    return {}


@operation("notification.subscribe_push", "Web-Push-Abo speichern.", True,
           obj({"endpoint": {"type": "string", "format": "https-url"}, "p256dh": s_str(), "auth": s_str()}), res_obj({}))
def subscribe_push(c, p):
    c.conn.execute("INSERT INTO push_subs(person, endpoint, p256dh, auth) VALUES (%s, %s, %s, %s)",
                   (c.person["sub"], p["endpoint"], p["p256dh"], p["auth"]))
    return {}


@operation("notification.test_push", "Test-Push an die eigenen Abos senden.", True, obj({}), res_obj({"event_id": UUID}))
def test_push(c, p):
    return {"event_id": emit(c, "notification.test", [c.person["sub"]], forced="webpush")}


DELIVERY = res_obj({"event_id": UUID, "event_type": STR, "correlation_id": STR, "trigger": {"type": "object"},
                    "recipient": STR, "channel": STR, "attempt": {"type": "integer"}, "result": STR, "at": UTCT,
                    "idempotency_key": STR})


@operation("notification.list", "Zustellprotokoll lesen (Auslöser oder Empfänger).", False,
           obj({"event_id": UUID, "correlation_id": STR, "limit": {"type": "integer", "minimum": 1, "maximum": 500}}, []),
           res_obj({"deliveries": {"type": "array", "items": DELIVERY}}))
def notification_list(c, p):
    sql, args = "SELECT * FROM deliveries WHERE (actor=%s OR recipient=%s)", [c.person["sub"], c.person["sub"]]
    if p.get("event_id"):
        sql += " AND event_id=%s"
        args.append(p["event_id"])
    if p.get("correlation_id"):
        sql += " AND corr=%s"
        args.append(p["correlation_id"])
    sql += " ORDER BY id LIMIT %s"
    args.append(p.get("limit", 100))
    out = []
    for r in c.conn.execute(sql, args).fetchall():
        d = {"event_id": str(r["event_id"]), "event_type": r["event_type"], "correlation_id": r["corr"], "trigger": r["trigger"],
             "recipient": r["recipient"], "channel": r["channel"], "attempt": r["attempt"], "result": r["result"],
             "at": ts(r["at"]), "idempotency_key": r["key"]}
        if r["error"]:
            d["error"] = r["error"]
        out.append(d)
    return {"deliveries": out}


@operation("cost.list", "Eigene Kostenposten lesen.", False,
           obj({"limit": {"type": "integer", "minimum": 1, "maximum": 500}}, []),
           res_obj({"entries": {"type": "array", "items": res_obj({"id": UUID, "at": UTCT, "person_id": STR, "provider": STR,
                                                                    "trigger": {"type": "object"}, "quantity": {"type": "object"},
                                                                    "amount_micro_eur": {"type": "integer"}})}}))
def cost_list(c, p):
    rows = q(c.conn, "SELECT * FROM costs WHERE person=%s ORDER BY at DESC LIMIT %s", c.person["sub"], p.get("limit", 100))
    return {"entries": [{"id": str(r["id"]), "at": ts(r["at"]), "person_id": r["person"], "provider": r["provider"],
                         "trigger": r["trigger"], "quantity": r["quantity"], "amount_micro_eur": r["amount"]} for r in rows]}


@operation("ai.ask", "KI um einen Vorschlag bitten (führt nichts aus).", False,
           obj({"prompt": s_str(1, 4000), "team_id": UUID}, ["prompt"]),
           res_obj({"text": STR, "proposed_calls": {"type": "array", "items": res_obj({"name": STR, "input": {"type": "object"}})},
                    "usage": res_obj({"input_tokens": {"type": "integer"}, "output_tokens": {"type": "integer"}})}))
def ai_ask(c, p):
    key = ENV("ANTHROPIC_API_KEY")
    if not key:
        raise ApiError(502, "provider_error", "kein ANTHROPIC_API_KEY konfiguriert")
    tools = tool_list()
    body = {"model": ENV("ANTHROPIC_MODEL", "claude-haiku-5-5"), "max_tokens": 1024, "tools": tools,
            "messages": [{"role": "user", "content": p["prompt"]}]}
    req = urllib.request.Request(ENV("ANTHROPIC_BASE_URL", "https://api.anthropic.com") + "/v1/messages", data=json.dumps(body).encode(), method="POST",
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except (urllib.error.URLError, TimeoutError) as ex:
        raise ApiError(502, "provider_error", f"KI-Anbieter: {ex}")
    back = {n.replace(".", "_"): n for n in OPS}
    calls = [{"name": back.get(b["name"], b["name"]), "input": b["input"]} for b in data["content"] if b["type"] == "tool_use"]
    text = "".join(b["text"] for b in data["content"] if b["type"] == "text")
    u = data["usage"]
    amount = round((u["input_tokens"] * int(ENV("AI_PRICE_IN_MICRO_EUR_PER_MTOK", "0")) + u["output_tokens"] * int(ENV("AI_PRICE_OUT_MICRO_EUR_PER_MTOK", "0"))) / 1e6)
    c.conn.execute("INSERT INTO costs VALUES (%s, now(), %s, 'anthropic', %s, %s, %s)",
                   (str(uuid.uuid4()), c.person["sub"], Jsonb({"kind": "operation", "name": "ai.ask", "correlation_id": c.corr}),
                    Jsonb({"input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"]}), amount))
    return {"text": text, "proposed_calls": calls, "usage": {"input_tokens": u["input_tokens"], "output_tokens": u["output_tokens"]}}


def tool_list():
    return [{"name": n.replace(".", "_"), "description": o["description"], "input_schema": o["params_schema"]} for n, o in OPS.items()]


def descriptor(o):
    return {k: o[k] for k in ("name", "description", "mutating", "preview_supported", "params_schema", "result_schema")}


# ------------------------------------------------------------------ Authentifizierung
_jwk = None


def jwk_client():
    global _jwk
    if _jwk is None:
        _jwk = PyJWKClient(f"{ISSUER}/protocol/openid-connect/certs", cache_keys=True)
    return _jwk


def verify_token(tok):
    try:
        key = jwk_client().get_signing_key_from_jwt(tok).key
        claims = jwt.decode(tok, key, algorithms=["RS256"], issuer=ISSUER, options={"verify_aud": False})
    except Exception:
        raise ApiError(401, "unauthenticated", "Token ungültig")
    return {"sub": claims["sub"], "name": claims.get("preferred_username", claims["sub"]), "email": claims.get("email")}


def upsert_person(pp):
    with connect() as c:
        c.execute("INSERT INTO persons(sub, name, email) VALUES (%s, %s, %s) ON CONFLICT (sub) DO UPDATE SET name=EXCLUDED.name, email=EXCLUDED.email",
                  (pp["sub"], pp["name"], pp["email"]))


def authenticate(headers):
    h = headers.get("Authorization", "")
    if h.startswith("Bearer "):
        pp = verify_token(h[7:])
    else:
        m = re.search(r"chronos_session=([^;\s]+)", headers.get("Cookie", ""))
        if not m:
            raise ApiError(401, "unauthenticated", "nicht angemeldet")
        with connect() as c:
            r = q1(c, "SELECT p.sub, p.name, p.email FROM sessions s JOIN persons p ON p.sub=s.person WHERE s.id=%s", m.group(1))
        if not r:
            raise ApiError(401, "unauthenticated", "Sitzung ungültig")
        return dict(r)
    upsert_person(pp)
    return pp


# ------------------------------------------------------------------ Web
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def send(self, status, obj_=None, headers=None, raw=None, ctype="application/json"):
        body = raw if raw is not None else (json.dumps(obj_).encode() if obj_ is not None else b"")
        self.send_response(status)
        if body or status not in (204, 302):
            self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Correlation-Id", self.corr)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def err(self, e):
        self.send(e.status, {"error": {"code": e.code, "message": e.message}})

    def handle_any(self, method):
        self.corr = (self.headers.get("X-Correlation-Id") or str(uuid.uuid4()))[:64]
        LOCAL.corr = self.corr
        t0 = time.time()
        status = 500
        try:
            status = self.route(method)
        except ApiError as e:
            status = e.status
            self.err(e)
        except InjectedFault as e:
            status = 500
            self.err(ApiError(500, "internal", str(e)))
        except Exception as e:
            log("error", "Unbehandelter Fehler", error=repr(e))
            status = 500
            self.err(ApiError(500, "internal", "interner Fehler"))
        log("info", "request", method=method, path=self.path.split("?")[0], status=status, ms=round((time.time() - t0) * 1000))

    def do_GET(self): self.handle_any("GET")
    def do_POST(self): self.handle_any("POST")

    def body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            raise ApiError(422, "validation_error", "kein gültiges JSON")

    def route(self, method):
        path = self.path.split("?")[0]
        if path == "/healthz":
            with connect() as c:
                c.execute("SELECT 1")
            return self.send(200, {"status": "ok"}) or 200
        if path == "/api/v1/operations" and method == "GET":
            return self.send(200, {"operations": [descriptor(o) for o in OPS.values()]}) or 200
        if path == "/api/v1/ai/tools" and method == "GET":
            return self.send(200, {"tools": tool_list()}) or 200
        if path == "/api/v1/push/vapid-public-key":
            return self.send(200, {"public_key": ENV("VAPID_PUBLIC_KEY", "")}) or 200
        if path.startswith("/static/"):
            f = os.path.join(ENV("STATIC_DIR", "./static"), os.path.basename(path))
            if os.path.isfile(f):
                ct = "text/html" if f.endswith(".html") else "application/javascript"
                return self.send(200, raw=open(f, "rb").read(), ctype=ct) or 200
            raise ApiError(404, "not_found", "Datei nicht gefunden")
        if path.startswith("/auth/"):
            return self.auth(method, path)
        m = re.match(r"^/api/v1/operations/([\w.]+)$", path)
        if m and method == "POST":
            return self.invoke(m.group(1))
        raise ApiError(404, "not_found", "unbekannter Pfad")

    def invoke(self, name):
        person = authenticate(self.headers)
        o = OPS.get(name)
        if not o:
            raise ApiError(404, "not_found", "unbekannte Operation")
        b = self.body()
        params = b.get("params", {})
        validate(o["params_schema"], params)
        preview = bool(b.get("preview")) and o["preview_supported"]
        with connect() as conn:
            c = Ctx(conn, person, self.corr, preview, self.headers.get("X-Spike-Fault"))
            c.operation = name
            result = o["fn"](c, params)
        if preview:
            return self.send(200, {"preview": result}) or 200
        return self.send(200, {"result": result}) or 200

    def auth(self, method, path):
        redirect = ENV("OIDC_REDIRECT_URL")
        endpoint = f"{ISSUER}/protocol/openid-connect"
        if path == "/auth/login":
            verifier = secrets.token_urlsafe(48)
            state = secrets.token_urlsafe(16)
            challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
            with connect() as c:
                c.execute("INSERT INTO auth_flows VALUES (%s, %s)", (state, verifier))
            qs = urllib.parse.urlencode({"client_id": ENV("OIDC_CLIENT_ID"), "response_type": "code", "scope": "openid email profile",
                                         "redirect_uri": redirect, "state": state, "code_challenge": challenge,
                                         "code_challenge_method": "S256"})
            return self.send(302, headers={"Location": f"{endpoint}/auth?{qs}"}) or 302
        if path == "/auth/callback":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            state, code = qs.get("state", [""])[0], qs.get("code", [""])[0]
            with connect() as c:
                f = q1(c, "DELETE FROM auth_flows WHERE state=%s RETURNING verifier", state)
            if not f:
                raise ApiError(400, "validation_error", "ungültiger state")
            data = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code, "redirect_uri": redirect,
                                           "client_id": ENV("OIDC_CLIENT_ID"), "client_secret": ENV("OIDC_CLIENT_SECRET"),
                                           "code_verifier": f["verifier"]}).encode()
            try:
                with urllib.request.urlopen(urllib.request.Request(f"{endpoint}/token", data=data), timeout=20) as r:
                    tok = json.load(r)
            except urllib.error.HTTPError:
                raise ApiError(400, "validation_error", "Codeaustausch fehlgeschlagen")
            pp = verify_token(tok["access_token"])
            upsert_person(pp)
            sid = secrets.token_urlsafe(32)
            with connect() as c:
                c.execute("INSERT INTO sessions VALUES (%s, %s)", (sid, pp["sub"]))
            return self.send(302, headers={"Location": "/", "Set-Cookie": f"chronos_session={sid}; HttpOnly; SameSite=Lax; Path=/"}) or 302
        if path == "/auth/me":
            p = authenticate(self.headers)
            return self.send(200, {"person_id": p["sub"], "name": p["name"], "email": p["email"]}) or 200
        if path == "/auth/logout" and method == "POST":
            m = re.search(r"chronos_session=([^;\s]+)", self.headers.get("Cookie", ""))
            if m:
                with connect() as c:
                    c.execute("DELETE FROM sessions WHERE id=%s", (m.group(1),))
            return self.send(204, headers={"Set-Cookie": "chronos_session=; Max-Age=0; HttpOnly; SameSite=Lax; Path=/"}) or 204
        raise ApiError(404, "not_found", "unbekannter Pfad")


# ------------------------------------------------------------------ Worker
def smtp_send(person, event, key, channel_corr):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = "chronos-spike@example.test", person["email"], f"Chronos: {event['type']}"
    msg["X-Chronos-Idempotency-Key"], msg["X-Chronos-Correlation-Id"] = key, channel_corr
    msg.set_content(f"Ereignis {event['type']} ({event['id']})")
    with smtplib.SMTP(ENV("SMTP_HOST"), int(ENV("SMTP_PORT")), timeout=10) as s:
        s.send_message(msg)


def deliver(channel, person, event, key, conn):
    if channel == "mock":
        req = urllib.request.Request(ENV("MOCK_CHANNEL_URL") + "/deliver", method="POST",
                                     data=json.dumps({"recipient": person["sub"], "event_type": event["type"], "event_id": str(event["id"]),
                                                      "correlation_id": event["corr"]}).encode(),
                                     headers={"Content-Type": "application/json", "Idempotency-Key": key})
        with urllib.request.urlopen(req, timeout=10):
            pass
        return "success", None
    if channel == "email":
        smtp_send(person, event, key, event["corr"])
        trig = event["trigger"]
        conn.execute("INSERT INTO costs VALUES (%s, now(), %s, 'smtp', %s, %s, %s)",
                     (str(uuid.uuid4()), trig["actor"], Jsonb({"kind": "operation", "name": trig.get("operation"), "correlation_id": event["corr"]}),
                      Jsonb({"messages": 1}), int(ENV("EMAIL_PRICE_MICRO_EUR", "0"))))
        return "success", None
    if channel == "webpush":
        if not q(conn, "SELECT 1 FROM push_subs WHERE person=%s", person["sub"]):
            return "skipped", "kein Abo"
        raise RuntimeError("Web Push in der Attrappe nicht implementiert")
    raise RuntimeError("unbekannter Kanal")


def process_task(lock_conn, task):
    event = q1(lock_conn, "SELECT * FROM events WHERE id=%s", task["event_id"])
    person = q1(lock_conn, "SELECT * FROM persons WHERE sub=%s", task["recipient"])
    LOCAL.corr = event["corr"]
    channels = [task["forced"]] if task["forced"] else person["channels"]
    with connect() as wc:
        wc.autocommit = True
        for ch in channels:
            key = f"{event['id']}:{person['sub']}:{ch}"
            for attempt in range(1, 4):
                result, error = None, None
                try:
                    result, error = deliver(ch, person, event, key, wc)
                except Exception as ex:
                    result, error = "failed", str(ex)[:200]
                wc.execute("INSERT INTO deliveries(event_id, event_type, corr, trigger, actor, recipient, channel, attempt, result, error, at, key)"
                           " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now(), %s)",
                           (event["id"], event["type"], event["corr"], Jsonb({k: event["trigger"][k] for k in ("kind", "actor")}),
                            event["trigger"]["actor"], person["sub"], ch, attempt, result, error, key))
                log("info", "Zustellversuch", event_id=str(event["id"]), channel=ch, attempt=attempt, result=result)
                if result in ("success", "skipped"):
                    break
                time.sleep(RETRY_BASE * (2 ** (attempt - 1)))
            if result == "success":
                return


def worker_loop():
    while True:
        try:
            with connect() as c:
                t = q1(c, "SELECT * FROM tasks WHERE state='pending' ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1")
                if not t:
                    time.sleep(0.2)
                    continue
                process_task(c, t)
                c.execute("UPDATE tasks SET state='done' WHERE id=%s", (t["id"],))
        except Exception as ex:
            log("error", "Worker-Fehler", error=repr(ex))
            time.sleep(1)


class Health(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        try:
            with connect() as c:
                c.execute("SELECT 1")
            body, code = b'{"status":"ok"}', 200
        except Exception:
            body, code = b'{"status":"down"}', 503
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "web"
    if mode == "web":
        migrate()
        log("info", "Web startet", port=ENV("PORT", "8080"))
        ThreadingHTTPServer(("0.0.0.0", int(ENV("PORT", "8080"))), Handler).serve_forever()
    elif mode == "worker":
        for i in range(60):  # auf das Schema warten
            try:
                with connect() as c:
                    c.execute("SELECT 1 FROM tasks LIMIT 1")
                break
            except Exception:
                time.sleep(1)
        threading.Thread(target=lambda: ThreadingHTTPServer(("0.0.0.0", int(ENV("WORKER_HEALTH_PORT", "8081"))), Health).serve_forever(), daemon=True).start()
        for _ in range(4):
            threading.Thread(target=worker_loop, daemon=True).start()
        log("info", "Worker startet")
        while True:
            time.sleep(3600)
    else:
        raise SystemExit("web oder worker")


if __name__ == "__main__":
    main()
