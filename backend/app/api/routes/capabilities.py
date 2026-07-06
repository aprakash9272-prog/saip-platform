from typing import Optional

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import PlainTextResponse

from app.api.deps import PaginationParams, SessionDep
from app.knowledge.exceptions import (
    DuplicateInBatchError,
    KnowledgeImportError,
    ReferenceNotFoundError,
    YAMLValidationError,
)
from app.knowledge.exporter import dump_capabilities_yaml
from app.knowledge.importer import KnowledgeImporter
from app.schemas.capability import CapabilityCreate, CapabilityRead, CapabilityUpdate
from app.schemas.common import PaginatedResponse
from app.schemas.domain import DomainRead
from app.services.capability import CapabilityService
from app.services.domain import DomainService

router = APIRouter(prefix="/capabilities", tags=["capabilities"])


@router.get("", response_model=PaginatedResponse[CapabilityRead], summary="List capabilities")
def list_capabilities(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    domain_id: Optional[int] = None,
    risk_category: Optional[str] = None,
):
    """List capabilities with free-text search plus exact-match domain/risk filters."""
    service = CapabilityService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={"domain_id": domain_id, "risk_category": risk_category},
    )
    return PaginatedResponse[CapabilityRead](
        items=list(items), total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/facets", summary="Get available filter values (domains + risk categories)")
def get_capability_facets(session: SessionDep):
    domain_service = DomainService(session)
    capability_service = CapabilityService(session)
    domains, _ = domain_service.list(limit=1000)
    return {
        "domains": [DomainRead.model_validate(d) for d in domains],
        "risk_categories": capability_service.list_risk_categories(),
    }


@router.get(
    "/export",
    response_class=PlainTextResponse,
    summary="Export all capabilities as YAML",
)
def export_capabilities(session: SessionDep):
    service = CapabilityService(session)
    yaml_text = dump_capabilities_yaml(service.export_all())
    return PlainTextResponse(yaml_text, media_type="application/x-yaml")


@router.post("/import", summary="Bulk import capabilities from a YAML file")
async def import_capabilities(
    session: SessionDep, file: UploadFile = File(...)
):
    """Validate and upsert capabilities from an uploaded YAML file.

    Referenced domains must already exist. Idempotent, like the CLI importer:
    re-uploading unchanged data reports everything as unchanged.
    """
    raw_bytes = await file.read()
    try:
        data = yaml.safe_load(raw_bytes)
    except yaml.YAMLError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Invalid YAML: {exc}") from exc

    if isinstance(data, dict):
        records = [data]
    elif isinstance(data, list):
        records = data
    else:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Expected a YAML mapping or a list of mappings.",
        )

    importer = KnowledgeImporter(session)
    try:
        summary = importer.import_capabilities_only(records)
    except (YAMLValidationError, DuplicateInBatchError, ReferenceNotFoundError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except KnowledgeImportError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return {
        "created": summary.created,
        "updated": summary.updated,
        "unchanged": summary.unchanged,
    }


@router.get("/{item_id}", response_model=CapabilityRead, summary="Get a single capability")
def get_capability(item_id: int, session: SessionDep):
    return CapabilityService(session).get(item_id)


@router.post(
    "",
    response_model=CapabilityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a capability",
)
def create_capability(payload: CapabilityCreate, session: SessionDep):
    return CapabilityService(session).create(payload.model_dump())


@router.put("/{item_id}", response_model=CapabilityRead, summary="Update a capability")
def update_capability(item_id: int, payload: CapabilityUpdate, session: SessionDep):
    return CapabilityService(session).update(item_id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a capability"
)
def delete_capability(item_id: int, session: SessionDep):
    CapabilityService(session).delete(item_id)
