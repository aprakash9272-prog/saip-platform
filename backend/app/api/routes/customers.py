from typing import Optional

from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationParams, SessionDep
from app.schemas.common import PaginatedResponse
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerUpdate
from app.services.customer import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=PaginatedResponse[CustomerRead], summary="List customers")
def list_customers(
    session: SessionDep,
    pagination: PaginationParams = Depends(),
    industry: Optional[str] = None,
):
    service = CustomerService(session)
    items, total = service.list(
        skip=pagination.skip,
        limit=pagination.limit,
        search=pagination.search,
        filters={"industry": industry},
        sort_by=pagination.sort_by,
        sort_desc=pagination.sort_desc,
    )
    return PaginatedResponse[CustomerRead](
        items=list(items), total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{item_id}", response_model=CustomerRead, summary="Get a single customer")
def get_customer(item_id: int, session: SessionDep):
    return CustomerService(session).get(item_id)


@router.post(
    "", response_model=CustomerRead, status_code=status.HTTP_201_CREATED, summary="Create a customer"
)
def create_customer(payload: CustomerCreate, session: SessionDep):
    return CustomerService(session).create(payload.model_dump())


@router.put("/{item_id}", response_model=CustomerRead, summary="Update a customer")
def update_customer(item_id: int, payload: CustomerUpdate, session: SessionDep):
    return CustomerService(session).update(item_id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a customer"
)
def delete_customer(item_id: int, session: SessionDep):
    CustomerService(session).delete(item_id)
