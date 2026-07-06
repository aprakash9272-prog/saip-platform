from fastapi import APIRouter, Depends, status

from app.api.deps import PaginationParams, SessionDep
from app.models.module import Module
from app.schemas.common import PaginatedResponse
from app.schemas.module import ModuleCreate, ModuleRead, ModuleUpdate
from app.services.module import ModuleService

router = APIRouter(prefix="/modules", tags=["modules"])


def _to_read(module: Module) -> ModuleRead:
    return ModuleRead(
        id=module.id,
        name=module.name,
        description=module.description,
        edition_id=module.edition_id,
        capability_ids=sorted(c.id for c in module.capabilities),
        created_at=module.created_at,
        updated_at=module.updated_at,
    )


@router.get("", response_model=PaginatedResponse[ModuleRead], summary="List modules")
def list_modules(session: SessionDep, pagination: PaginationParams = Depends()):
    service = ModuleService(session)
    items, total = service.list(
        skip=pagination.skip, limit=pagination.limit, search=pagination.search
    )
    return PaginatedResponse[ModuleRead](
        items=[_to_read(m) for m in items],
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{module_id}", response_model=ModuleRead, summary="Get a module")
def get_module(module_id: int, session: SessionDep):
    service = ModuleService(session)
    return _to_read(service.get(module_id))


@router.post(
    "",
    response_model=ModuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a module",
)
def create_module(payload: ModuleCreate, session: SessionDep):
    service = ModuleService(session)
    return _to_read(service.create(payload.model_dump()))


@router.put("/{module_id}", response_model=ModuleRead, summary="Update a module")
def update_module(module_id: int, payload: ModuleUpdate, session: SessionDep):
    service = ModuleService(session)
    return _to_read(service.update(module_id, payload.model_dump(exclude_unset=True)))


@router.delete(
    "/{module_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a module"
)
def delete_module(module_id: int, session: SessionDep):
    service = ModuleService(session)
    service.delete(module_id)
