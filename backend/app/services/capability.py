from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError
from app.models.capability import Capability
from app.repositories.capability import CapabilityRepository
from app.services.base import BaseService


class CapabilityService(BaseService[Capability]):
    entity_name = "Capability"

    def __init__(self, session: Session):
        super().__init__(CapabilityRepository(session))

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        code = data.get("code")
        if code is None:
            return
        existing = self.repository.get_by_code(code)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError("Capability", f"code={code!r}")
