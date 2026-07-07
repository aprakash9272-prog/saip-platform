from typing import Optional

from sqlmodel import Session

from app.models.customer import Customer
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    search_fields = ("name", "industry", "description", "headquarters")

    def __init__(self, session: Session):
        super().__init__(session, Customer)

    def get_by_name(self, name: str) -> Optional[Customer]:
        return self.get_by(name=name)
