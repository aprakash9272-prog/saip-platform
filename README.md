# saip-platform

Open Source AI Security Architecture Intelligence Platform

See [docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md) for the full product and architecture blueprint.

## Project Status

**Sprint 9 — Security Recommendation Engine.** Building directly on Sprint 8's `GapEngine`, `RecommendationEngine` recommends the catalog products, modules, and configurations that would close each identified gap — deterministically, from existing `ProductCapabilityMapping` rows, with **no AI/LLM reasoning**. For every addressable gap it surfaces every candidate product (module, license tier, deployment model, platform support), a confidence score, implementation complexity, estimated effort, and a 4-tier priority (Critical/High/Medium/Low) ranked from gap severity, business criticality, framework impact, and implementation effort. The report also forecasts coverage improvement and estimated risk reduction if every recommendation were implemented, plus a cross-gap product comparison. Reports are exportable as JSON, Excel, or PDF, and a dedicated Recommendations page (executive summary, top recommendations, coverage forecast, priority matrix, product comparison, and a filterable/sortable/searchable recommendation table) is linked from every Assessment Project. Builds on Sprint 8's Gap Analysis Engine, Sprint 7's Coverage Analysis Engine, Sprint 6's Customer Assessment Workspace, and Sprint 5's `ProductCapabilityMapping` fact table. Simulation, Overlap Analysis, and AI Assistant engines are still not implemented.

## Monorepo Structure

```
backend/    FastAPI + SQLModel + Alembic service, PostgreSQL-backed
  app/models/       SQLModel table definitions
  app/schemas/      Pydantic request/response schemas
  app/repositories/ Data-access layer
  app/services/     Business rules (uniqueness, referential checks, bulk ops)
  app/api/routes/   FastAPI routers (thin controllers)
  app/knowledge/    YAML knowledge base + importer/exporter (see below)
  app/engine/       Analysis engines — coverage_engine.py, gap_engine.py, and
                    recommendation_engine.py implemented (Sprints 7-9); overlap/simulation/cost
                    engines still placeholders
  tests/            pytest suite (importer, validation, API, engine unit/perf tests)
frontend/   Next.js 15 + TypeScript + Tailwind CSS + shadcn/ui dashboard
  src/app/(dashboard)/knowledge-base/    Knowledge Base pages (vendors, products, ...)
  src/app/(dashboard)/customers/         Customer list + detail (business units, environments, assessments)
  src/app/(dashboard)/assessments/[id]/  Assessment project page (dashboard, coverage analysis, product
                                          assignments, import/export)
  src/app/(dashboard)/assessments/[id]/gaps/            Dedicated Gap Analysis page
  src/app/(dashboard)/assessments/[id]/recommendations/ Dedicated Recommendations page
  src/components/knowledge-base/         Config-driven CRUD table/form/detail components
  src/components/customers/              Customer detail + business unit/environment/assessment dialogs
  src/components/assessments/            Assessment project page, product assignment wizard, coverage
                                          analysis section, the Gap Analysis page, and the
                                          Recommendations page (forecast, priority matrix, product
                                          comparison, recommendation table with filters/search/sort)
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

## Customer Assessment Workspace

The customer/project layer represents a real organization's security environment — the input that future Coverage, Gap, Overlap, Recommendation, Simulation, and AI engines will read from.

```
Customer
 ├── Business Units       divisions/departments within the customer
 ├── Environments         Production, UAT, Development, DR, OT
 └── Assessment Projects  a security assessment engagement
      └── Product Assignments   an existing Vendor/Product/Edition (+ Modules) deployed
                                into one Environment, with license quantity, deployment
                                model, deployment status, and notes
```

Product Assignments always reference existing Sprint 5 knowledge-base records (Vendor, Product, Edition, Module) — they never duplicate product definitions. Referential integrity is enforced end-to-end: a Product must belong to its Vendor, an Edition to its Product, a Module to its Edition, and an Environment to the same Customer as the Assessment Project it's used in. A unique constraint on `(assessment_project, edition, environment)` prevents duplicate assignments.

Each Assessment Project exposes an **informational dashboard** (`GET /assessment-projects/{id}/dashboard`) summarizing total deployed products, vendors in use, modules enabled, capabilities available, security domains represented, and frameworks represented — derived transitively through the Module → Capability → Domain/Framework chain. This is a rollup only; no coverage, gap, or overlap scoring is computed yet.

Assessments support JSON export/import (`GET/POST /assessment-projects/{id}/export`, `POST /assessment-projects/import`) keyed by natural names (customer name, vendor/product/edition/module names, environment name) rather than raw database ids, so an export never leaks internal ids and re-importing an unchanged export reports every project/assignment as `unchanged`.

## Coverage Analysis Engine

`CoverageEngine` (`backend/app/engine/coverage_engine.py`) calculates, for a single assessment project, how much of the vendor-neutral capability catalog is actually covered by its deployed products. It is a pure calculation — no gap remediation, no overlap scoring, no recommendations; those are separate future engines.

**Only Product Assignments with `deployment_status == "Deployed"` count.** A product that is Not Started, In Progress, or Decommissioned is not actually protecting the environment today, so it does not contribute coverage — this is the key distinction from Sprint 6's informational dashboard, which counts every assignment regardless of status.

For every capability in the catalog, the engine determines:

- **Covered** — provided by at least one deployed assignment's module.
- **Missing** — provided by none.
- **Duplicate** — provided by more than one *different* deployed product (two modules on the *same* assignment providing the same capability is not a duplicate — that's one product, not redundancy).

It then rolls this up into:

- **Domain coverage** — covered/total/percentage for every one of the 18 security domains in the taxonomy (Identity & Access Management, Endpoint Security, Network Security, Cloud Security, Application Security, Data Security & Privacy, Threat Intelligence, Security Operations & Incident Response, Vulnerability & Exposure Management, Governance Risk & Compliance, Email & Collaboration Security, Zero Trust & Network Access, DevSecOps & Software Supply Chain Security, API Security, Container & Kubernetes Security, IoT & OT Security, Encryption & Key Management, Business Continuity & Disaster Recovery).
- **Overall coverage score** — covered capabilities ÷ total capabilities across the whole catalog.

A `CoverageReport` can be exported as **JSON**, **Excel** (multi-sheet workbook: summary, domain coverage, covered/missing/duplicate capability lists), or **PDF** (a formatted, paginated report) via `GET /analysis/coverage/{id}/export?format=`.

On the Assessment Project page, the **Coverage Analysis** section shows a coverage score card, covered/missing/duplicate summary cards, a covered-vs-missing pie chart, a per-domain coverage bar chart, a domain heatmap, and a filterable capability matrix table — plus the JSON/Excel/PDF export buttons.

## Gap Analysis Engine

`GapEngine` (`backend/app/engine/gap_engine.py`) is built directly on top of `CoverageEngine` — it takes the coverage report's missing-capability list and classifies each one for risk triage. Like the Coverage Engine, it is a pure calculation: identification and classification only, no remediation recommendations.

For every missing capability, the engine determines:

- **Severity** (Critical / High / Medium / Low / Informational) — a deterministic score built from the capability's risk category (Critical/High/Medium/Low, from the knowledge base), how many compliance framework controls map to it, and whether it's flagged `is_business_critical` (a new boolean on `Capability`, defaulting to `false`, settable via the API, the Capabilities UI, or YAML import/export). Risk category alone lands on a sensible baseline tier (Critical → High, High → High, Medium → Medium, Low → Low); framework mapping count and business-criticality are what escalate a gap into the top Critical tier.
- **Business impact** (Severe / High / Moderate / Low) — a related but distinct classification driven primarily by business-criticality, since a capability's operational impact isn't purely a function of technical risk.
- **Framework controls** — every compliance control (framework name/version, control id/name) mapped to the missing capability, from the Sprint 3 framework mapping table.
- **Mapped products** — vendor/product/edition combinations in the knowledge base already known to provide this capability (via Sprint 5's `ProductCapabilityMapping`), regardless of whether they're deployed in this assessment. This is informational enumeration, not a ranked recommendation.
- **Status** — always `"Open"`; acknowledging, accepting risk on, or remediating a gap is a manual workflow concern, out of scope for both the Gap and Recommendation Engines.

It then rolls this up into **domain gap scores** (coverage %, gap %, missing count, critical gap count, and a blended 0-100 domain risk score — half gap percentage, half average gap severity) for every domain, plus an overall gap percentage and overall risk score for the assessment.

A `GapReport` exports as **JSON**, **Excel** (Summary / Domain Gap Scores / Gaps sheets), or **PDF** via `GET /analysis/gaps/export?assessment_id=&format=`.

A dedicated **Gap Analysis** page (`/assessments/{id}/gaps`, linked from the Assessment Project page) shows an executive summary (overall risk score, gap counts by severity), a Critical Gap card grid, a domain risk heatmap, a severity × business-impact risk matrix, and a gap table with search, severity/domain filters, sortable columns, and bar charts (gaps by severity, gaps by domain) — plus the JSON/Excel/PDF export buttons.

## Recommendation Engine

`RecommendationEngine` (`backend/app/engine/recommendation_engine.py`) is built directly on top of `GapEngine` — for every gap in the gap report, it looks up every `ProductCapabilityMapping` catalog row for that capability and turns each one into a candidate recommendation. **Everything here is deterministic and knowledge-base-driven: no AI, no LLM, no generated text.** A gap with zero catalog candidates is counted as *unaddressable* and produces no recommendation — there's nothing to recommend.

For every candidate product, the engine computes:

- **Confidence score** (0-100) — from the product's availability status (Generally Available scores highest, Discontinued lowest), plus a +15 bonus if the vendor is already deployed elsewhere in the assessment (a known vendor relationship is a safer bet).
- **Implementation complexity** (Low/Medium/High) — from the deployment model (SaaS is easiest, Hybrid hardest), downgraded one tier if the vendor is already deployed (adding a module/license to an existing relationship is easier than onboarding a new vendor).
- **Estimated effort** — a bucketed string derived from complexity (`"1-2 weeks"` / `"2-6 weeks"` / `"6-12 weeks"`).
- **Required license tier, deployment model, and platform support** — read straight off the `ProductCapabilityMapping` row.

Candidates for a gap are ranked confidence-first; the top-ranked candidate is used to compute that gap's **priority** (Critical/High/Medium/Low) — a deterministic score from the gap's severity, business impact, framework-control count, the best candidate's implementation complexity (an easy win is prioritized over a hard one, all else equal), and whether closing this gap would meaningfully move an unusually small domain's coverage. Each recommendation also reports its **estimated risk reduction**: the precise before/after delta in the assessment's overall risk score if that one gap were closed (not just a qualitative label).

The report rolls up into a **coverage improvement forecast** (current vs. projected coverage % if every addressable gap were closed), a **priority matrix** (recommendation counts per tier), and a **product comparison** (which catalog products address the most gaps, with average confidence and domains covered) — useful for spotting a single vendor that could close several gaps at once.

A `RecommendationReport` exports as **JSON**, **Excel** (Summary / Priority Matrix / Product Comparison / Recommendations sheets), or **PDF** via `GET /analysis/recommendations/export?assessment_id=&format=`.

A dedicated **Recommendations** page (`/assessments/{id}/recommendations`, linked from the Assessment Project page) shows an executive summary (estimated risk reduction, addressable/unaddressable counts, priority counts), a coverage improvement forecast bar, a Top Recommendations card grid (Critical/High priority), a priority-matrix bar chart, a product comparison table, and a full recommendation table with search, priority/domain filters, and sortable columns — plus the JSON/Excel/PDF export buttons.

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

The Customer Assessment Workspace adds:

```
GET/POST        /customers            /business-units       /environments
GET/POST        /assessment-projects  /product-assignments
GET/PUT/DELETE  .../{id}
```

```
GET  /business-units?customer_id=
GET  /environments?customer_id=&environment_type=
GET  /assessment-projects?customer_id=&status=
GET  /product-assignments?assessment_project_id=&vendor_id=&product_id=&edition_id=
                          &environment_id=&deployment_model=&deployment_status=

GET  /assessment-projects/{id}/dashboard   informational rollup (see above)
GET  /assessment-projects/{id}/export      export the project + assignments as JSON
POST /assessment-projects/import           idempotent upsert import from JSON
```

All list endpoints (including every knowledge base entity above) also accept `?sort_by=<column>&sort_desc=true|false`.

The Coverage Analysis Engine adds:

```
POST /analysis/coverage                        body: {"assessment_project_id": <id>} -> CoverageReport
GET  /analysis/coverage/{assessment_id}         the same CoverageReport, by id
GET  /analysis/coverage/{assessment_id}/export  ?format=json|excel|pdf -> file download
GET  /analysis/domain-summary?assessment_id=    just the per-domain coverage breakdown
GET  /analysis/capabilities?assessment_id=      the covered/missing/duplicate capability matrix
```

The Gap Analysis Engine adds:

```
POST /analysis/gaps                          body: {"assessment_project_id": <id>} -> GapReport
GET  /analysis/gaps/{assessment_id}           the same GapReport, by id
GET  /analysis/gaps/export?assessment_id=     ?format=json|excel|pdf -> file download
GET  /analysis/gaps/summary?assessment_id=    executive summary only (no gap/domain lists)
GET  /analysis/gaps/domains?assessment_id=    just the per-domain gap score breakdown
```

The Recommendation Engine adds:

```
POST /analysis/recommendations                          body: {"assessment_project_id": <id>} -> RecommendationReport
GET  /analysis/recommendations/{assessment_id}           the same RecommendationReport, by id
GET  /analysis/recommendations/export?assessment_id=     ?format=json|excel|pdf -> file download
GET  /analysis/recommendations/summary?assessment_id=    executive summary only (no recommendation/matrix/comparison lists)
```

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

**Customers** (`/customers`) lists onboarded customers. Selecting one opens its detail page (`/customers/{id}`), with tables for Business Units, Environments, and Assessment Projects, each with inline create/edit/delete. Selecting an Assessment Project opens `/assessments/{id}`: the informational dashboard cards, a **Coverage Analysis** section (score card, pie/bar charts, domain heatmap, capability matrix, JSON/Excel/PDF export), a Product Assignments table, and Import JSON / Export JSON buttons. **Add Product** opens a two-step wizard — vendor → product → edition, then modules/environment/license/deployment details — that only ever references existing knowledge-base records.

The **Gap Analysis** button on the Assessment Project page opens `/assessments/{id}/gaps`: an executive summary, a Critical Gap card grid, gaps-by-severity and gaps-by-domain bar charts, a domain risk heatmap, a severity × business-impact risk matrix, and a gap table with search, severity/domain filters, sortable columns, and JSON/Excel/PDF export.

The **Recommendations** button opens `/assessments/{id}/recommendations`: an executive summary (estimated risk reduction, priority counts), a coverage improvement forecast bar, a Top Recommendations card grid, a priority-matrix bar chart, a product comparison table, and a recommendation table with search, priority/domain filters, sortable columns, and JSON/Excel/PDF export.

## Makefile Reference

Run `make help` for the full list of available commands (docker-compose lifecycle, backend migrations/lint/tests, knowledge base import/export, frontend dev/build/lint).

## Documentation

- [Project Blueprint](docs/PROJECT_BLUEPRINT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Spec](docs/API_SPEC.md)
- [Database](docs/DATABASE.md)
- [Roadmap](docs/ROADMAP.md)
