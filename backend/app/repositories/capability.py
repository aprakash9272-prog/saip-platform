from typing import Optional

from sqlmodel import Session

from app.models.capability import Capability
from app.repositories.base import BaseRepository


class CapabilityRepository(BaseRepository[Capability]):
    search_fields = ("name", "code", "domain", "description", "risk_category")

    def __init__(self, session: Session):
        super().__init__(session, Capability)

    def get_by_code(self, code: str) -> Optional[Capability]:
        return self.get_by(code=code)
