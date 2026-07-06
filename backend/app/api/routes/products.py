from app.api.routes.factory import build_crud_router
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product import ProductService

router = build_crud_router(
    prefix="/products",
    tags=["products"],
    service_factory=ProductService,
    read_schema=ProductRead,
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
)
