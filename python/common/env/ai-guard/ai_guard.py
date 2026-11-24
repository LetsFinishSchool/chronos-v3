"""KI-Schutz-Proxy für die Spikes (V-6): hält den echten Schlüssel und erzwingt harte Grenzen.

Die Spike-Anwendungen sprechen mit ANTHROPIC_BASE_URL (diesen Proxy) und kennen den echten Schlüssel nie.
Erlaubt ist nur POST /v1/messages ohne Streaming, mit dem konfigurierten Modell; max_tokens wird gedeckelt.
Grenzen je Proxy-Lebensdauer (Neustart setzt zurück): Anfragen, Eingabe- und Ausgabetokens. Danach 429.
Zusätzlich gilt ein Ausgabenlimit in der Anthropic-Konsole (nicht prüfbar); dies ist die technische Grenze davor.
"""
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-5-5")
UPSTREAM = os.environ.get("AI_GUARD_UPSTREAM", "https://api.anthropic.com")
MAX_REQ = int(os.environ.get("AI_GUARD_MAX_REQUESTS", "150"))
MAX_IN = int(os.environ.get("AI_GUARD_MAX_INPUT_TOKENS", "600000"))
MAX_OUT = int(os.environ.get("AI_GUARD_MAX_OUTPUT_TOKENS", "60000"))
CAP_TOKENS = int(os.environ.get("AI_GUARD_MAX_TOKENS_PER_CALL", "1024"))
LOCK = threading.Lock()
USED = {"requests": 0, "input_tokens": 0, "output_tokens": 0, "rejected": 0}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def deny(self, code, msg):
        with LOCK:
            USED["rejected"] += 1
        self.send_json(code, {"type": "error", "error": {"type": "guard_error", "message": msg}})

    def do_GET(self):
        if self.path in ("/healthz", "/guard/stats"):
            return self.send_json(200, {"status": "ok", "used": USED,
                                        "limits": {"requests": MAX_REQ, "input_tokens": MAX_IN, "output_tokens": MAX_OUT}})
        self.send_json(404, {"error": "unbekannt"})

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        if self.path.split("?")[0] != "/v1/messages":
            return self.deny(403, "nur /v1/messages erlaubt")
        try:
            body = json.loads(raw)
        except ValueError:
            return self.deny(400, "kein JSON")
        if body.get("stream"):
            return self.deny(400, "Streaming ist im Spike nicht erlaubt")
        if body.get("model") != MODEL:
            return self.deny(403, f"nur das Modell {MODEL} ist erlaubt")
        body["max_tokens"] = min(int(body.get("max_tokens", CAP_TOKENS)), CAP_TOKENS)
        if not KEY:
            return self.deny(503, "kein Schlüssel im Proxy konfiguriert")
        with LOCK:
            if USED["requests"] >= MAX_REQ or USED["input_tokens"] >= MAX_IN or USED["output_tokens"] >= MAX_OUT:
                USED["rejected"] += 1
                return self.send_json(429, {"type": "error", "error": {"type": "guard_budget_exhausted", "message": "Spike-Budget aufgebraucht"}})
            USED["requests"] += 1  # vor dem Aufruf zählen: auch Fehlversuche verbrauchen Budget
        req = urllib.request.Request(UPSTREAM + "/v1/messages", data=json.dumps(body).encode(), method="POST",
                                     headers={"x-api-key": KEY, "anthropic-version": self.headers.get("anthropic-version", "2023-06-01"),
                                              "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                data, code = r.read(), r.status
        except urllib.error.HTTPError as e:
            data, code = e.read(), e.code
        except (urllib.error.URLError, TimeoutError) as e:
            return self.send_json(502, {"type": "error", "error": {"type": "upstream_error", "message": str(e)[:200]}})
        try:
            u = json.loads(data).get("usage") or {}
            with LOCK:
                USED["input_tokens"] += int(u.get("input_tokens", 0))
                USED["output_tokens"] += int(u.get("output_tokens", 0))
        except (ValueError, AttributeError):
            pass
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("AI_GUARD_PORT", "8099"))), H).serve_forever()
