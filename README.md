# saip-platform

Open Source AI Security Architecture Intelligence Platform

See [docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md) for the full product and architecture blueprint.

## Project Status

**Sprint 3 — Security Knowledge Base Foundation.** The platform now has a normalized knowledge base (vendors, products, editions, modules, capabilities, frameworks, framework mappings), a YAML-driven importer, full CRUD APIs, and a Knowledge Base section in the dashboard. No analysis logic (coverage, gap, overlap, recommendation, simulation, AI) has been implemented yet — this sprint only builds the knowledge foundation those future engines will read from.

## Monorepo Structure

```
backend/    FastAPI + SQLModel + Alembic service, PostgreSQL-backed
  app/models/       SQLModel table definitions
  app/schemas/      Pydantic request/response schemas
  app/repositories/ Data-access layer
  app/services/     Business rules (uniqueness, referential checks)
  app/api/routes/   FastAPI routers (thin controllers)
  app/knowledge/    YAML knowledge base + importer (see below)
  app/engine/       Future analysis engines (coverage/gap/overlap/...) — not implemented yet
  tests/            pytest suite (importer, validation, API)
frontend/   Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui dashboard
  src/app/(dashboard)/knowledge-base/   Knowledge Base pages (vendors, products, ...)
  src/components/knowledge-base/        Config-driven CRUD table/form/detail components
docs/       Product blueprint and architecture documentation
```

## Prerequisites

- Docker and Docker Compose
- Node.js 22+ and npm (for local frontend development)
- Python 3.11+ (for local backend development)

## Quick Start (Docker Compose)

```bash
cp .env.example .env
make up
```

This starts three services and automatically applies database migrations on backend startup:

| Service  | URL                            |
| -------- | ------------------------------ |
| frontend | http://localhost:3000          |
| backend  | http://localhost:8000          |
| API docs | http://localhost:8000/docs     |
| postgres | localhost:5432                 |

Stop the stack with `make down`.

## Security Knowledge Base

The knowledge base lives at `backend/app/knowledge/` as YAML files, organized by entity:

```
backend/app/knowledge/
  vendors/        Vendor definitions
  products/       Products (reference a vendor by name)
  editions/       Editions (reference a vendor + product by name)
  modules/        Modules (reference vendor + product + edition; list capability codes provided)
  capabilities/   The vendor-neutral capability taxonomy (unique code per capability)
  frameworks/     Compliance/security frameworks (e.g. NIST CSF)
  mappings/       Capability → framework control mappings
```

A small two-vendor sample (CrowdStrike Falcon and SentinelOne Singularity, both providing an overlapping EDR capability) ships in these folders as a working example.

Import the knowledge base into the database:

```bash
make kb-import            # validates and imports; safe to re-run (idempotent)
make kb-import-dry-run     # validates only, no database writes
```

Or directly, matching the required CLI form:

```bash
python -m app.knowledge.import_all
python -m app.knowledge.import_all --path /custom/knowledge --dry-run
```

The importer:
- Validates every YAML record against a Pydantic schema before touching the database.
- Imports in a fixed order — Vendor, Product, Edition, Module, Capability, Framework, Mapping — resolving each reference against already-imported rows (rejecting unknown vendor/product/edition/capability/framework references with a clear error).
- Rejects duplicate natural keys within the same import batch (e.g. two vendor files with the same name).
- Runs a generic dependency-graph cycle check across the batch before writing anything.
- Is idempotent: re-running against unchanged YAML reports everything as `unchanged`; changed fields report as `updated`; new records report as `created`. Nothing is ever duplicated.

## Backend APIs

Full CRUD + search + pagination is available for every knowledge base entity, documented in Swagger at `/docs`:

```
GET/POST     /vendors        /products      /editions      /modules
GET/POST     /capabilities   /frameworks    /mappings
GET/PUT/DELETE  .../{id}
```

List endpoints accept `?search=`, `?skip=`, `?limit=` and return a paginated envelope (`items`, `total`, `skip`, `limit`).

## Local Development

### Backend

```bash
cd backend
cp .env.example .env
make backend-install     # creates backend/.venv and installs requirements.txt
make backend-run         # runs uvicorn with reload on http://localhost:8000
```

Database migrations (requires PostgreSQL running, e.g. via `make up`):

```bash
make backend-migrate                      # apply migrations
make backend-revision msg="add x table"   # generate a new revision
```

Tests:

```bash
make backend-test        # pytest: importer, YAML validation, and API tests (sqlite in-memory)
```

### Frontend

```bash
cd frontend
cp .env.example .env
make frontend-install
make frontend-dev        # runs Next.js dev server on http://localhost:3000
```

The Knowledge Base pages live under **Knowledge Base** in the sidebar (`/knowledge-base/vendors`, `/products`, `/editions`, `/modules`, `/capabilities`, `/frameworks`, `/mappings`). Each page supports search, pagination, create, edit, delete, and a read-only detail view.

## Makefile Reference

Run `make help` for the full list of available commands (docker-compose lifecycle, backend migrations/lint/tests, knowledge base import, frontend dev/build/lint).

## Documentation

- [Project Blueprint](docs/PROJECT_BLUEPRINT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Spec](docs/API_SPEC.md)
- [Database](docs/DATABASE.md)
- [Roadmap](docs/ROADMAP.md)
