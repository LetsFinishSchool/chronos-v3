#!/usr/bin/env bash
# Läuft in der VM als agent: gibt ein frisches Keycloak-Token für alice aus (Port des Keycloak als Argument).
python3 ~/eval/common/env/get_token.py alice "http://localhost:$1"
