from typing import Optional

from sqlmodel import Session

from app.models.business_unit import BusinessUnit
from app.repositories.base import BaseRepository


class BusinessUnitRepository(BaseRepository[BusinessUnit]):
    search_fields = ("name", "description")

    def __init__(self, session: Session):
        super().__init__(session, BusinessUnit)

    def get_by_customer_and_name(
        self, customer_id: int, name: str
    ) -> Optional[BusinessUnit]:
        return self.get_by(customer_id=customer_id, name=name)
