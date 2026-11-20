IMAGE ?= chronos-spike-rust
BASE_URL ?= http://localhost:10080

.PHONY: build test arch-check bridge

build:
	docker build -t $(IMAGE) .

test:
	cargo test

arch-check:
	./tools/arch-check.sh

# Erzeugt bridge/generated/ aus GET $(BASE_URL)/api/v1/operations (der Dienst läuft dabei).
bridge:
	cd tools && npm install --no-audit --no-fund --silent
	BASE_URL=$(BASE_URL) node tools/bridge-gen.mjs
