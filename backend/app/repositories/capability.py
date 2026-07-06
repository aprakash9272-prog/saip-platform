from typing import List, Optional

from sqlmodel import Session

from app.models.capability import Capability
from app.repositories.base import BaseRepository


class CapabilityRepository(BaseRepository[Capability]):
    search_fields = ("name", "code", "description", "risk_category")

    def __init__(self, session: Session):
        super().__init__(session, Capability)

    def get_by_code(self, code: str) -> Optional[Capability]:
        return self.get_by(code=code)

    def list_risk_categories(self) -> List[str]:
        return self.distinct_values("risk_category")

    def all(self) -> List[Capability]:
        items, _ = self.list(skip=0, limit=1_000_000)
        return items
