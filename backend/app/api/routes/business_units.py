from typing import Optional

from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationParams, SessionDep
from app.schemas.business_unit import (
    BusinessUnitCreate,
    BusinessUnitRead,
    BusinessUnitUpdate,
)
from app.schemas.common import PaginatedResponse
from app.services.business_unit import BusinessUnitService

router = APIRouter(prefix="/business-units", tags=["business-units"])


@router.get(
    "", response_model=PaginatedResponse[BusinessUnitRead], summary="List business units"
)
def list_business_units(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    customer_id: Optional[int] = None,
):
    service = BusinessUnitService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={"customer_id": customer_id},
        sort_by=pagination.sort_by,
        sort_desc=pagination.sort_desc,
    )
    return PaginatedResponse[BusinessUnitRead](
        items=list(items), total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get(
    "/{item_id}", response_model=BusinessUnitRead, summary="Get a single business unit"
)
def get_business_unit(item_id: int, session: SessionDep):
    return BusinessUnitService(session).get(item_id)


@router.post(
    "",
    response_model=BusinessUnitRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a business unit",
)
def create_business_unit(payload: BusinessUnitCreate, session: SessionDep):
    return BusinessUnitService(session).create(payload.model_dump())


@router.put(
    "/{item_id}", response_model=BusinessUnitRead, summary="Update a business unit"
)
def update_business_unit(item_id: int, payload: BusinessUnitUpdate, session: SessionDep):
    return BusinessUnitService(session).update(
        item_id, payload.model_dump(exclude_unset=True)
    )


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a business unit"
)
def delete_business_unit(item_id: int, session: SessionDep):
    BusinessUnitService(session).delete(item_id)
