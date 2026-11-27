# One image for web, worker and migration job; the subcommand picks the role
# (ADR-002, ADR-011, ADR-013).

FROM lukemathwalker/cargo-chef:0.1.78-rust-1.100.0-slim-trixie AS chef
WORKDIR /app

# Static SPA build (ADR-007); the web process serves it from CHRONOS_FRONTEND_DIR.
FROM node:22.21.1-trixie-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
COPY frontend/app/package.json app/package.json
RUN npm ci
COPY frontend/app app
RUN npm run build

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
# `query!` reads .sqlx instead of a database at compile time.
ENV SQLX_OFFLINE=true
COPY --from=planner /app/recipe.json recipe.json
RUN cargo chef cook --release --locked --recipe-path recipe.json
COPY . .
RUN cargo build --release --locked --bin chronos

# distroless/cc brings glibc, CA certificates and tzdata, but no shell;
# debug with `kubectl debug` (ADR-013).
FROM gcr.io/distroless/cc-debian13:nonroot
COPY --from=builder /app/target/release/chronos /usr/local/bin/chronos
COPY --from=frontend /frontend/app/build /usr/local/share/chronos/frontend
ENV CHRONOS_FRONTEND_DIR=/usr/local/share/chronos/frontend
ENTRYPOINT ["/usr/local/bin/chronos"]
CMD ["serve"]
