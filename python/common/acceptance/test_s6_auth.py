"""S-6 / K4: Bearer-Prüfung und OIDC-Code-Flow mit PKCE gegen Keycloak (skriptgesteuert)."""
import html
from http import cookiejar
import unittest
import urllib.parse
import urllib.request

from spikelib import *
from spikelib import _NoRedirect


def _opener():
    # Keycloak setzt Secure-Cookies; Browser behandeln http://localhost als sicher, Python nicht: Richtlinie anpassen
    jar = cookiejar.CookieJar(cookiejar.DefaultCookiePolicy(secure_protocols=("http", "https")))
    return urllib.request.build_opener(_NoRedirect, urllib.request.HTTPCookieProcessor(jar)), jar


class K4Auth(unittest.TestCase):
    def test_K4_bearer_accepted(self):
        r = alice().raw("GET", "/auth/me")
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json["person_id"], alice().sub)
        self.assertEqual(r.json["name"], "alice")
        self.assertEqual(r.json["email"], USERS["alice"])

    def test_K4_bad_tokens_rejected(self):
        good = token("alice")
        head, payload, sig = good.split(".")
        forged = ".".join([head, payload, sig[:-4] + ("AAAA" if not sig.endswith("AAAA") else "BBBB")])
        for label, t in (("manipulierte Signatur", forged), ("Müll", "abc"), ("leer", "")):
            with self.subTest(label):
                r = http("GET", BASE_URL + "/auth/me", headers={"Authorization": f"Bearer {t}"})
                self.assertEqual(r.status, 401, r)
        self.assertEqual(http("GET", BASE_URL + "/auth/me").status, 401)

    def test_K4_code_flow_with_pkce_and_logout(self):
        op, jar = _opener()
        r = http("GET", BASE_URL + "/auth/login", opener=op)
        self.assertEqual(r.status, 302, r)
        loc = r.headers["Location"]
        q = urllib.parse.parse_qs(urllib.parse.urlparse(loc).query)
        self.assertEqual(q.get("response_type"), ["code"], loc)
        self.assertEqual(q.get("code_challenge_method"), ["S256"], "PKCE (S256) fehlt")
        self.assertTrue(q.get("code_challenge") and q.get("state"), loc)
        page = http("GET", loc, opener=op)
        self.assertEqual(page.status, 200, f"Keycloak-Anmeldeseite: {page}")
        m = re.search(r'<form[^>]*id="kc-form-login"[^>]*action="([^"]+)"', page.raw) or \
            re.search(r'<form[^>]*action="([^"]+)"[^>]*id="kc-form-login"', page.raw)
        self.assertTrue(m, "Anmeldeformular nicht gefunden (Keycloak-Theme?)")
        post = http("POST", html.unescape(m.group(1)), form={"username": "alice", "password": PASSWORD,
                                                             "credentialId": ""}, opener=op)
        self.assertEqual(post.status, 302, f"Anmeldung nicht angenommen: {post.raw[:300]}")
        cb = post.headers["Location"]
        self.assertTrue(cb.startswith(BASE_URL + "/auth/callback"), f"Umleitung nicht auf Chronos: {cb}")
        done = http("GET", cb, opener=op)
        self.assertEqual(done.status, 302, f"Callback: {done}")
        cookie = done.headers.get("Set-Cookie", "")
        self.assertIn("chronos_session=", cookie)
        self.assertIn("httponly", cookie.lower())
        self.assertIn("samesite=lax", cookie.lower())
        me = http("GET", BASE_URL + "/auth/me", opener=op)
        self.assertEqual(me.status, 200, me)
        self.assertEqual(me.json["person_id"], alice().sub)
        session = next(c for c in jar if c.name == "chronos_session")
        out = http("POST", BASE_URL + "/auth/logout", opener=op)
        self.assertEqual(out.status, 204, out)
        stale = http("GET", BASE_URL + "/auth/me", headers={"Cookie": f"chronos_session={session.value}"})
        self.assertEqual(stale.status, 401, "Sitzung nach Abmeldung serverseitig noch gültig")

    def test_K4_callback_rejects_wrong_state(self):
        r = http("GET", BASE_URL + "/auth/callback?code=x&state=bogus")
        self.assertEqual(r.status, 400, r)


if __name__ == "__main__":
    unittest.main()
