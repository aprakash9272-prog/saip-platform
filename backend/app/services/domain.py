from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError
from app.models.domain import Domain
from app.repositories.domain import DomainRepository
from app.services.base import BaseService


class DomainService(BaseService[Domain]):
    entity_name = "Domain"

    def __init__(self, session: Session):
        super().__init__(DomainRepository(session))

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        name = data.get("name")
        if name is None:
            return
        existing = self.repository.get_by_name(name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError("Domain", f"name={name!r}")
