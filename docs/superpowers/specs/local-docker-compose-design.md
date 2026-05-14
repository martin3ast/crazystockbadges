# Local docker-compose deploy

_Date: 2026-05-13_

## Purpose

Provide a local deployment method for Crazy Stock Badges using `docker compose`, alongside the existing Cloud Run deploy (`deploy.sh`). The existing `Dockerfile` is reused unchanged.

## Scope

Add a `docker-compose.yml` at the repo root with two profiles:

- `prod` — prod-parity smoke test of the image that `deploy.sh` ships.
- `dev` — local development with bind-mounted source and Flask debug hot-reload.

Append a short "Local deploy with Docker Compose" section to `README.md` documenting the two commands.

Out of scope: changes to `Dockerfile`, changes to `deploy.sh`, reverse proxy, multi-host orchestration, separate dev Dockerfile.

## Services

### `app` (profile: `prod`)

- `build: .` (reuses existing Dockerfile)
- `env_file: .env`
- Environment overrides: `LOG_LEVEL=INFO`, `FLASK_DEBUG=False`
- Port mapping: `5000:5000`
- Named volumes for runtime artifacts so output survives `docker compose down`:
  - `cache:/app/cache`
  - `scad_models:/app/scad_models`
  - `stl_models:/app/stl_models`
  - `data:/app/data`
- `restart: unless-stopped`

### `dev` (profile: `dev`)

- Same `build: .`
- `env_file: .env`
- Environment overrides: `FLASK_DEBUG=True`, `LOG_LEVEL=DEBUG`
- Port mapping: `5000:5000`
- Bind-mount repo to `/app` so source edits hot-reload via Flask debug
- Bind-mount host directories for runtime artifacts (so they land in the working tree, not a named volume):
  - `./cache:/app/cache`
  - `./scad_models:/app/scad_models`
  - `./stl_models:/app/stl_models`
  - `./data:/app/data`
- `restart: "no"`

## Top-level volumes

Named volumes declared for the `prod` profile: `cache`, `scad_models`, `stl_models`, `data`.

## Usage (documented in README.md)

```
docker compose --profile prod up --build      # prod-parity, port 5000
docker compose --profile dev up --build       # dev w/ hot reload, port 5000
docker compose down
```

Prerequisite: a populated `.env` file (see `ENV_SETUP.md`) with at least `OPENROUTER_API_KEY`.

## Acceptance

- `docker compose --profile prod up --build` starts the app on `http://localhost:5000`.
- `docker compose --profile dev up --build` starts the app on `http://localhost:5000` with `FLASK_DEBUG=True`, and edits to `app.py` on the host reload inside the container.
- `docker compose down` cleanly stops the stack; named volumes persist between runs.
- `Dockerfile` and `deploy.sh` are unchanged.
