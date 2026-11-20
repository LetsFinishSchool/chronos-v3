# syntax=docker/dockerfile:1
# Stufe 1: Abhängigkeiten (Cache-Schicht, ändert sich nur mit Cargo.toml/Cargo.lock)
FROM rust:1-bookworm AS deps
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo 'fn main() {}' > src/main.rs && cargo build --release && rm -rf src target/release/deps/chronos* target/release/chronos*

# Stufe 2: Anwendung
FROM deps AS build
COPY migrations ./migrations
COPY src ./src
RUN touch src/main.rs && cargo build --release && cp target/release/chronos /chronos

# Stufe 3: schlankes Laufzeitabbild, Nicht-Root
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends libssl3 ca-certificates && rm -rf /var/lib/apt/lists/* \
 && useradd --system --uid 10001 --no-create-home chronos
COPY --from=build /chronos /usr/local/bin/chronos
USER 10001
ENV LOG_FORMAT=json PORT=8080 WORKER_HEALTH_PORT=8081
ENTRYPOINT ["/usr/local/bin/chronos"]
CMD ["web"]
