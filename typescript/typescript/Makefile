IMAGE ?= chronos-spike-typescript
BASE_URL ?= http://localhost:8080

.PHONY: build test arch-check bridge
node_modules: package.json package-lock.json
	npm ci
	@touch node_modules

build:
	docker build -t $(IMAGE) .

test: node_modules
	npx tsc --noEmit -p .
	npx vitest run

arch-check: node_modules
	npx depcruise src --config .dependency-cruiser.cjs

bridge: node_modules
	BASE_URL=$(BASE_URL) npx tsx scripts/bridge.ts
