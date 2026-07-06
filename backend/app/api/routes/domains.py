from app.api.routes.factory import build_crud_router
from app.schemas.domain import DomainCreate, DomainRead, DomainUpdate
from app.services.domain import DomainService

router = build_crud_router(
    prefix="/domains",
    tags=["domains"],
    service_factory=DomainService,
    read_schema=DomainRead,
    create_schema=DomainCreate,
    update_schema=DomainUpdate,
)
