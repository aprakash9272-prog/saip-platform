from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.repositories.vendor import VendorRepository
from app.services.base import BaseService


class ProductService(BaseService[Product]):
    entity_name = "Product"

    def __init__(self, session: Session):
        super().__init__(ProductRepository(session))
        self.vendor_repository = VendorRepository(session)

    def validate_references(self, data: dict) -> None:
        vendor_id = data.get("vendor_id")
        if vendor_id is not None and self.vendor_repository.get(vendor_id) is None:
            raise InvalidReferenceError(f"Vendor with id={vendor_id} does not exist.")

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        vendor_id = data.get("vendor_id")
        name = data.get("name")
        if vendor_id is None or name is None:
            return
        existing = self.repository.get_by_vendor_and_name(vendor_id, name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "Product", f"vendor_id={vendor_id}, name={name!r}"
            )
