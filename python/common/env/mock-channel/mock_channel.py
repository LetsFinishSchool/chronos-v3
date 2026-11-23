"""Mock-Kanal für die Spikes (V-1 §6). Nur Standardbibliothek."""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOCK = threading.Lock()
STATE = {"fail_for": set(), "latency_ms": 50, "keys": {}, "deliveries": [], "duplicates": 0}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, obj=None):
        body = json.dumps(obj if obj is not None else {}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}") if n else {}

    def do_GET(self):
        if self.path == "/stats":
            with LOCK:
                s = {"effective": len(STATE["deliveries"]), "duplicates": STATE["duplicates"],
                     "keys": dict(STATE["keys"]), "deliveries": list(STATE["deliveries"])}
            return self._send(200, s)
        if self.path == "/healthz":
            return self._send(200, {"status": "ok"})
        self._send(404)

    def do_POST(self):
        b = self._body()
        if self.path == "/reset":
            with LOCK:
                STATE.update(keys={}, deliveries=[], duplicates=0)
            return self._send(200)
        if self.path == "/control":
            with LOCK:
                if "fail_for" in b:
                    STATE["fail_for"] = set(b["fail_for"])
                if "latency_ms" in b:
                    STATE["latency_ms"] = int(b["latency_ms"])
            return self._send(200)
        if self.path == "/deliver":
            time.sleep(STATE["latency_ms"] / 1000)
            key = self.headers.get("Idempotency-Key")
            if not key:
                return self._send(400, {"error": "Idempotency-Key fehlt"})
            with LOCK:
                if b.get("recipient") in STATE["fail_for"]:
                    return self._send(503, {"error": "simulierter Fehler"})
                if key in STATE["keys"]:
                    STATE["keys"][key] += 1
                    STATE["duplicates"] += 1
                    return self._send(200, {"duplicate": True})
                STATE["keys"][key] = 1
                STATE["deliveries"].append({"key": key, "recipient": b.get("recipient"),
                                            "correlation_id": b.get("correlation_id")})
            return self._send(200, {"duplicate": False})
        self._send(404)


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("MOCK_PORT", "8090"))), H).serve_forever()
