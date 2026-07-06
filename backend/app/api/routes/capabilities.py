from app.api.routes.factory import build_crud_router
from app.schemas.capability import CapabilityCreate, CapabilityRead, CapabilityUpdate
from app.services.capability import CapabilityService

router = build_crud_router(
    prefix="/capabilities",
    tags=["capabilities"],
    service_factory=CapabilityService,
    read_schema=CapabilityRead,
    create_schema=CapabilityCreate,
    update_schema=CapabilityUpdate,
)
