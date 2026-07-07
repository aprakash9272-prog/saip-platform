from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.business_unit import BusinessUnit
from app.repositories.business_unit import BusinessUnitRepository
from app.repositories.customer import CustomerRepository
from app.services.base import BaseService


class BusinessUnitService(BaseService[BusinessUnit]):
    entity_name = "BusinessUnit"

    def __init__(self, session: Session):
        super().__init__(BusinessUnitRepository(session))
        self.customer_repository = CustomerRepository(session)

    def validate_references(self, data: dict) -> None:
        customer_id = data.get("customer_id")
        if customer_id is not None and self.customer_repository.get(customer_id) is None:
            raise InvalidReferenceError(f"Customer with id={customer_id} does not exist.")

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        customer_id = data.get("customer_id")
        name = data.get("name")
        if customer_id is None or name is None:
            return
        existing = self.repository.get_by_customer_and_name(customer_id, name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "BusinessUnit", f"customer_id={customer_id}, name={name!r}"
            )
