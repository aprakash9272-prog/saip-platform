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
from app.knowledge.exporter import dump_product_mappings_yaml
from app.knowledge.importer import KnowledgeImporter
from app.schemas.common import PaginatedResponse
from app.schemas.product_capability_mapping import (
    BulkOperationResult,
    ProductCapabilityMappingBulkDelete,
    ProductCapabilityMappingBulkUpdate,
    ProductCapabilityMappingCreate,
    ProductCapabilityMappingRead,
    ProductCapabilityMappingUpdate,
)
from app.services.product_capability_mapping import ProductCapabilityMappingService

router = APIRouter(prefix="/product-mappings", tags=["product-mappings"])


@router.get(
    "",
    response_model=PaginatedResponse[ProductCapabilityMappingRead],
    summary="List product capability mappings",
)
def list_product_mappings(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    vendor_id: Optional[int] = None,
    product_id: Optional[int] = None,
    edition_id: Optional[int] = None,
    module_id: Optional[int] = None,
    capability_id: Optional[int] = None,
    deployment_model: Optional[str] = None,
    availability_status: Optional[str] = None,
    licensing_tier: Optional[str] = None,
):
    """List mappings with free-text search plus exact-match filters across
    every dimension of the hierarchy and mapping metadata."""
    service = ProductCapabilityMappingService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={
            "vendor_id": vendor_id,
            "product_id": product_id,
            "edition_id": edition_id,
            "module_id": module_id,
            "capability_id": capability_id,
            "deployment_model": deployment_model,
            "availability_status": availability_status,
            "licensing_tier": licensing_tier,
        },
        sort_by=pagination.sort_by,
        sort_desc=pagination.sort_desc,
    )
    return PaginatedResponse[ProductCapabilityMappingRead](
        items=list(items), total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/facets", summary="Get available filter values for product mappings")
def get_product_mapping_facets(session: SessionDep):
    service = ProductCapabilityMappingService(session)
    return service.list_facets()


@router.get(
    "/export",
    response_class=PlainTextResponse,
    summary="Export all product capability mappings as YAML",
)
def export_product_mappings(session: SessionDep):
    service = ProductCapabilityMappingService(session)
    yaml_text = dump_product_mappings_yaml(service.export_all())
    return PlainTextResponse(yaml_text, media_type="application/x-yaml")


@router.post("/import", summary="Bulk import product capability mappings from a YAML file")
async def import_product_mappings(session: SessionDep, file: UploadFile = File(...)):
    """Validate and upsert mappings from an uploaded YAML file.

    Referenced vendors/products/editions/modules/capabilities must already
    exist. Idempotent: re-uploading unchanged data reports everything as
    unchanged.
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
        summary = importer.import_product_mappings_only(records)
    except (YAMLValidationError, DuplicateInBatchError, ReferenceNotFoundError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    except KnowledgeImportError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return {
        "created": summary.created,
        "updated": summary.updated,
        "unchanged": summary.unchanged,
    }


@router.patch(
    "/bulk",
    response_model=BulkOperationResult,
    summary="Bulk-update a set of product capability mappings",
)
def bulk_update_product_mappings(
    payload: ProductCapabilityMappingBulkUpdate, session: SessionDep
):
    service = ProductCapabilityMappingService(session)
    updated, failed = service.bulk_update(
        payload.ids, payload.patch.model_dump(exclude_unset=True)
    )
    return BulkOperationResult(updated=updated, failed=failed)


@router.delete(
    "/bulk",
    response_model=BulkOperationResult,
    summary="Bulk-delete a set of product capability mappings",
)
def bulk_delete_product_mappings(
    payload: ProductCapabilityMappingBulkDelete, session: SessionDep
):
    service = ProductCapabilityMappingService(session)
    deleted, failed = service.bulk_delete(payload.ids)
    return BulkOperationResult(deleted=deleted, failed=failed)


@router.get(
    "/{item_id}",
    response_model=ProductCapabilityMappingRead,
    summary="Get a single product capability mapping",
)
def get_product_mapping(item_id: int, session: SessionDep):
    return ProductCapabilityMappingService(session).get(item_id)


@router.post(
    "",
    response_model=ProductCapabilityMappingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product capability mapping",
)
def create_product_mapping(payload: ProductCapabilityMappingCreate, session: SessionDep):
    return ProductCapabilityMappingService(session).create(payload.model_dump())


@router.put(
    "/{item_id}",
    response_model=ProductCapabilityMappingRead,
    summary="Update a product capability mapping",
)
def update_product_mapping(
    item_id: int, payload: ProductCapabilityMappingUpdate, session: SessionDep
):
    return ProductCapabilityMappingService(session).update(
        item_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product capability mapping",
)
def delete_product_mapping(item_id: int, session: SessionDep):
    ProductCapabilityMappingService(session).delete(item_id)
