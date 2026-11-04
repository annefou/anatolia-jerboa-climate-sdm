FROM ghcr.io/prefix-dev/pixi:0.68.1

LABEL org.opencontainers.image.source="https://github.com/annefou/anatolia-jerboa-climate-sdm"
LABEL org.opencontainers.image.description="Replication study container for anatolia-jerboa-climate-sdm"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

# git is needed by pixi to install healpix-connector, a git dependency in pixi.toml; the pixi base image has none.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install the pinned environment first (separate from source copy so the lock
# layer is cached across source-only edits).
COPY pixi.toml pixi.lock /app/
RUN pixi install --locked

COPY . /app

# Mount any required credentials at runtime, e.g.:
#   docker run -v ~/.cdsapirc:/home/mambauser/.cdsapirc anatolia-jerboa-climate-sdm
# See data/README.md for per-dataset credential setup.

CMD ["pixi", "run", "snakemake", "--cores", "1"]
