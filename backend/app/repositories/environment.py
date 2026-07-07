from typing import Optional

from sqlmodel import Session

from app.models.environment import Environment
from app.repositories.base import BaseRepository


class EnvironmentRepository(BaseRepository[Environment]):
    search_fields = ("name", "description")

    def __init__(self, session: Session):
        super().__init__(session, Environment)

    def get_by_customer_and_name(
        self, customer_id: int, name: str
    ) -> Optional[Environment]:
        return self.get_by(customer_id=customer_id, name=name)
