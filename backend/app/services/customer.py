from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError
from app.models.customer import Customer
from app.repositories.customer import CustomerRepository
from app.services.base import BaseService


class CustomerService(BaseService[Customer]):
    entity_name = "Customer"

    def __init__(self, session: Session):
        super().__init__(CustomerRepository(session))

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        name = data.get("name")
        if name is None:
            return
        existing = self.repository.get_by_name(name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError("Customer", f"name={name!r}")
