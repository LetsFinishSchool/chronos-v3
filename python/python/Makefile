IMAGE ?= chronos-spike-python
# uv lokal, sonst im Container (Werkzeug-Image; Umgebung und Cache außerhalb des Projekts)
UV ?= $(if $(shell command -v uv 2>/dev/null),uv,docker run --rm -u $(shell id -u):$(shell id -g) \
  -e UV_CACHE_DIR=/tmp/uv-cache -e UV_PROJECT_ENVIRONMENT=/tmp/venv -e HOME=/tmp \
  -v $(CURDIR):/w -w /w ghcr.io/astral-sh/uv:python3.13-bookworm-slim uv)
BASE_URL ?= http://localhost:13080
BRIDGE_TOOLS ?= npx --yes

.PHONY: build test arch-check bridge lock

build:
	docker build -t $(IMAGE) .

lock:
	$(UV) lock

# Eigene Tests (laufen im Container mit Dev-Abhängigkeiten, ohne Dienste)
test:
	$(UV) run --frozen pytest -q tests

# Architekturregel S-9: Fachbereiche (chronos.domain) kennen Kanäle (chronos.channels) nicht. Exit-Code != 0 bei Verstoß.
arch-check:
	$(UV) run --frozen lint-imports

# Frontend-Brücke S-10: Typen aus GET $(BASE_URL)/api/v1/operations (Dienst muss laufen)
bridge:
	BASE_URL=$(BASE_URL) python3 bridge/generate.py
