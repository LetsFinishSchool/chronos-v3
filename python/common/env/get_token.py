#!/usr/bin/env python3
"""Gibt ein Keycloak-Zugangstoken aus (für den manuellen Web-Push-Test). Aufruf: get_token.py alice [KEYCLOAK_URL]"""
import json, sys, urllib.parse, urllib.request
user = sys.argv[1] if len(sys.argv) > 1 else "alice"
kc = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8180"
data = urllib.parse.urlencode({"grant_type": "password", "client_id": "chronos-spike-test", "username": user,
                               "password": "spike-pass", "scope": "openid email profile"}).encode()
print(json.load(urllib.request.urlopen(f"{kc}/realms/chronos-spike/protocol/openid-connect/token", data))["access_token"])
