# ── Stage 1: Build ──
FROM rust:1-bookworm AS builder

WORKDIR /build

# Copy manifest first for dependency caching
COPY Cargo.toml Cargo.lock* ./

# Create dummy src for dependency compilation
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release 2>/dev/null || true

# Copy real source
COPY src/ src/

# Touch main.rs to invalidate the dummy cached build
RUN touch src/main.rs

# Build the real binary
RUN cargo build --release

# ── Stage 2: Runtime ──
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libssl3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/rhinometric-anomaly-engine /usr/local/bin/anomaly-engine

# Config directory (hot-reloadable)
COPY config/ /app/config/
WORKDIR /app

# Non-root user
RUN useradd -r -s /bin/false anomaly
USER anomaly

ENV RUST_LOG=info

EXPOSE 8091

CMD ["anomaly-engine"]
