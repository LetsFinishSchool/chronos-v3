IMAGE ?= chronos-spike-go
BASE_URL ?= http://localhost:9080

.PHONY: build test arch-check bridge generate

build:
	docker build -t $(IMAGE) .

generate:
	sqlc generate

test:
	go vet ./...
	go test ./...

# Architekturregel V-1 §9: Fachbereiche (internal/domain) dürfen die Kanäle (internal/channels) nicht kennen,
# auch nicht indirekt (go list -deps, einschließlich Testabhängigkeiten).
arch-check:
	@bad=$$(go list -test -deps -f '{{.ImportPath}}' ./internal/domain/... | grep -E '^chronos/internal/(channels|worker)' || true); \
	if [ -n "$$bad" ]; then echo "VERSTOSS: internal/domain haengt von den Kanaelen ab:"; echo "$$bad"; exit 1; fi; \
	echo "arch-check: ok"

bridge:
	cd bridge && npm install --no-audit --no-fund --silent && BASE_URL=$(BASE_URL) node gen.mjs
