from app.api.routes.factory import build_crud_router
from app.schemas.vendor import VendorCreate, VendorRead, VendorUpdate
from app.services.vendor import VendorService

router = build_crud_router(
    prefix="/vendors",
    tags=["vendors"],
    service_factory=VendorService,
    read_schema=VendorRead,
    create_schema=VendorCreate,
    update_schema=VendorUpdate,
)
