from typing import List, Optional

from sqlmodel import Session

from app.models.domain import Domain
from app.repositories.base import BaseRepository


class DomainRepository(BaseRepository[Domain]):
    search_fields = ("name", "description")

    def __init__(self, session: Session):
        super().__init__(session, Domain)

    def get_by_name(self, name: str) -> Optional[Domain]:
        return self.get_by(name=name)

    def all(self) -> List[Domain]:
        items, _ = self.list(skip=0, limit=1_000_000)
        return items
