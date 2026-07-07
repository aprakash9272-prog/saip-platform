# saip-platform

Open Source AI Security Architecture Intelligence Platform

See [docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md) for the full product and architecture blueprint.

## Project Status

**Sprint 5 — Product Capability Mapping.** The knowledge base now has its core mapping layer: a `ProductCapabilityMapping` fact table linking vendor → product → edition → module → capability, with licensing tier, supported platforms, deployment model, and availability status. Populated with 16 real mappings across 7 named vendors (CrowdStrike, Microsoft, SentinelOne, Trellix, Palo Alto Networks, Okta, Splunk). Builds on Sprint 4's domain taxonomy (18 domains, 324 capabilities) and the Sprint 3 foundation (vendors, products, editions, modules, frameworks, framework mappings). No analysis logic (coverage, gap, overlap, recommendation, simulation, AI) has been implemented yet — these sprints only build the knowledge foundation those future engines will read from.

## Monorepo Structure

```
backend/    FastAPI + SQLModel + Alembic service, PostgreSQL-backed
  app/models/       SQLModel table definitions
  app/schemas/      Pydantic request/response schemas
  app/repositories/ Data-access layer
  app/services/     Business rules (uniqueness, referential checks, bulk ops)
  app/api/routes/   FastAPI routers (thin controllers)
  app/knowledge/    YAML knowledge base + importer/exporter (see below)
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
  vendors/            Vendor definitions
  products/           Products (reference a vendor by name)
  editions/           Editions (reference a vendor + product by name)
  modules/            Modules (reference vendor + product + edition; list capability codes provided)
  domains/            The security domain taxonomy (18 domains, e.g. Endpoint Security, Zero Trust & Network Access)
  capabilities/       Vendor-neutral capability catalog (324 capabilities, ~18 per domain), each referencing a domain by name
  frameworks/         Compliance/security frameworks (e.g. NIST CSF)
  mappings/           Capability → framework control mappings
  product_mappings/   Vendor/product/edition/module → capability mappings, with licensing tier,
                      supported platforms, deployment model, and availability status
```

A working sample ships in these folders: 7 named vendors (CrowdStrike, Microsoft, SentinelOne, Trellix, Palo Alto Networks, Okta, Splunk) each with a product/edition/module hierarchy, the full 18-domain / 324-capability catalog, a NIST CSF mapping example, and 16 product-capability mappings — including EDR-001 appearing across 5 different vendors, real overlap data ready for future coverage/gap/overlap engines to consume.

Import the knowledge base into the database:

```bash
make kb-import            # validates and imports; safe to re-run (idempotent)
make kb-import-dry-run     # validates only, no database writes
make kb-export             # exports the current DB back to backend/exports/knowledge/ as YAML
```

Or directly, matching the required CLI form:

```bash
python -m app.knowledge.import_all
python -m app.knowledge.import_all --path /custom/knowledge --dry-run
python -m app.knowledge.export_all
```

The importer:
- Validates every YAML record against a Pydantic schema before touching the database.
- Imports in a fixed order — Vendor, Product, Edition, Module, Domain, Capability, Framework, Mapping, Product Mapping — resolving each reference against already-imported rows (rejecting unknown references with a clear error, and for product mappings, requiring the referenced module and capability to already exist).
- Rejects duplicate natural keys within the same import batch.
- Runs a generic dependency-graph cycle check across the batch before writing anything.
- Is idempotent: re-running against unchanged YAML reports everything as `unchanged`; changed fields report as `updated`; new records report as `created`. Nothing is ever duplicated.

`export_all` deliberately writes to `backend/exports/knowledge/` rather than back into `app/knowledge/`, so re-running `import_all` against the source tree never sees duplicate records.

## Backend APIs

Full CRUD + search + pagination is available for every knowledge base entity, documented in Swagger at `/docs`:

```
GET/POST     /vendors        /products      /editions      /modules
GET/POST     /domains        /capabilities  /frameworks    /mappings
GET/POST     /product-mappings
GET/PUT/DELETE  .../{id}
```

List endpoints accept `?search=`, `?skip=`, `?limit=` (max 500) and return a paginated envelope (`items`, `total`, `skip`, `limit`). Capabilities additionally support:

```
GET  /capabilities?domain_id=&risk_category=   filter by domain and/or risk category
GET  /capabilities/facets                      available domains + risk categories for building filter UIs
GET  /capabilities/export                      all capabilities as YAML (text/plain)
POST /capabilities/import                      bulk upsert capabilities from an uploaded YAML file
```

Product mappings — the core mapping layer — additionally support:

```
GET    /product-mappings?vendor_id=&product_id=&edition_id=&module_id=&capability_id=
                          &deployment_model=&availability_status=&licensing_tier=
GET    /product-mappings/facets    available deployment models, availability statuses, licensing tiers
GET    /product-mappings/export    all mappings as YAML (text/plain)
POST   /product-mappings/import    bulk upsert mappings from an uploaded YAML file
PATCH  /product-mappings/bulk      apply one partial update to a set of mapping ids
DELETE /product-mappings/bulk      delete a set of mapping ids
```

`ProductCapabilityMapping` enforces a uniqueness constraint on `(module, capability, licensing_tier, deployment_model)` to prevent duplicate mappings, and validates that the vendor/product/edition/module chain is internally consistent (e.g. a product must actually belong to the given vendor) before allowing a write.

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

The Knowledge Base pages live under **Knowledge Base** in the sidebar (`/knowledge-base/vendors`, `/products`, `/editions`, `/modules`, `/domains`, `/capabilities`, `/frameworks`, `/mappings`, `/product-mappings`). Each page supports search, pagination, create, edit, delete, and a read-only detail view.

- **Capabilities** additionally has domain/risk-category filter dropdowns and Import YAML / Export YAML buttons.
- **Product Mappings** additionally has vendor/deployment-model/availability-status/licensing-tier filter dropdowns, Import YAML / Export YAML buttons, and **bulk editing**: select rows via checkboxes to bulk-set availability status or bulk-delete.

## Makefile Reference

Run `make help` for the full list of available commands (docker-compose lifecycle, backend migrations/lint/tests, knowledge base import/export, frontend dev/build/lint).

## Documentation

- [Project Blueprint](docs/PROJECT_BLUEPRINT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Spec](docs/API_SPEC.md)
- [Database](docs/DATABASE.md)
- [Roadmap](docs/ROADMAP.md)
