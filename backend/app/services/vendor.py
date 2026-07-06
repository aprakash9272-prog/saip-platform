from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError
from app.models.vendor import Vendor
from app.repositories.vendor import VendorRepository
from app.services.base import BaseService


class VendorService(BaseService[Vendor]):
    entity_name = "Vendor"

    def __init__(self, session: Session):
        super().__init__(VendorRepository(session))

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        name = data.get("name")
        if name is None:
            return
        existing = self.repository.get_by_name(name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError("Vendor", f"name={name!r}")
