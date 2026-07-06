from typing import List, Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.capability import Capability
from app.repositories.capability import CapabilityRepository
from app.repositories.domain import DomainRepository
from app.services.base import BaseService


class CapabilityService(BaseService[Capability]):
    entity_name = "Capability"

    def __init__(self, session: Session):
        super().__init__(CapabilityRepository(session))
        self.domain_repository = DomainRepository(session)

    def validate_references(self, data: dict) -> None:
        domain_id = data.get("domain_id")
        if domain_id is not None and self.domain_repository.get(domain_id) is None:
            raise InvalidReferenceError(f"Domain with id={domain_id} does not exist.")

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        code = data.get("code")
        if code is None:
            return
        existing = self.repository.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError("Capability", f"code={code!r}")

    def list_risk_categories(self) -> List[str]:
        return self.repository.list_risk_categories()

    def export_all(self) -> List[Capability]:
        return self.repository.all()
