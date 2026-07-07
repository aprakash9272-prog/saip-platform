from typing import Optional

from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationParams, SessionDep
from app.models.product_assignment import ProductAssignment
from app.schemas.common import PaginatedResponse
from app.schemas.product_assignment import (
    ProductAssignmentCreate,
    ProductAssignmentRead,
    ProductAssignmentUpdate,
)
from app.services.product_assignment import ProductAssignmentService

router = APIRouter(prefix="/product-assignments", tags=["product-assignments"])


def _to_read(assignment: ProductAssignment) -> ProductAssignmentRead:
    return ProductAssignmentRead(
        id=assignment.id,
        assessment_project_id=assignment.assessment_project_id,
        vendor_id=assignment.vendor_id,
        product_id=assignment.product_id,
        edition_id=assignment.edition_id,
        environment_id=assignment.environment_id,
        license_quantity=assignment.license_quantity,
        deployment_model=assignment.deployment_model,
        deployment_status=assignment.deployment_status,
        notes=assignment.notes,
        module_ids=sorted(m.id for m in assignment.modules),
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


@router.get(
    "",
    response_model=PaginatedResponse[ProductAssignmentRead],
    summary="List product assignments",
)
def list_product_assignments(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    assessment_project_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    product_id: Optional[int] = None,
    edition_id: Optional[int] = None,
    environment_id: Optional[int] = None,
    deployment_model: Optional[str] = None,
    deployment_status: Optional[str] = None,
):
    service = ProductAssignmentService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={
            "assessment_project_id": assessment_project_id,
            "vendor_id": vendor_id,
            "product_id": product_id,
            "edition_id": edition_id,
            "environment_id": environment_id,
            "deployment_model": deployment_model,
            "deployment_status": deployment_status,
        },
        sort_by=pagination.sort_by,
        sort_desc=pagination.sort_desc,
    )
    return PaginatedResponse[ProductAssignmentRead](
        items=[_to_read(i) for i in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{item_id}",
    response_model=ProductAssignmentRead,
    summary="Get a single product assignment",
)
def get_product_assignment(item_id: int, session: SessionDep):
    return _to_read(ProductAssignmentService(session).get(item_id))


@router.post(
    "",
    response_model=ProductAssignmentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product assignment",
)
def create_product_assignment(payload: ProductAssignmentCreate, session: SessionDep):
    return _to_read(ProductAssignmentService(session).create(payload.model_dump()))


@router.put(
    "/{item_id}",
    response_model=ProductAssignmentRead,
    summary="Update a product assignment",
)
def update_product_assignment(
    item_id: int, payload: ProductAssignmentUpdate, session: SessionDep
):
    return _to_read(
        ProductAssignmentService(session).update(
            item_id, payload.model_dump(exclude_unset=True)
        )
    )


@router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product assignment",
)
def delete_product_assignment(item_id: int, session: SessionDep):
    ProductAssignmentService(session).delete(item_id)
