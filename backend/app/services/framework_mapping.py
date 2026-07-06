from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.framework_mapping import FrameworkMapping
from app.repositories.capability import CapabilityRepository
from app.repositories.framework import FrameworkRepository
from app.repositories.framework_mapping import FrameworkMappingRepository
from app.services.base import BaseService


class FrameworkMappingService(BaseService[FrameworkMapping]):
    entity_name = "FrameworkMapping"

    def __init__(self, session: Session):
        super().__init__(FrameworkMappingRepository(session))
        self.capability_repository = CapabilityRepository(session)
        self.framework_repository = FrameworkRepository(session)

    def validate_references(self, data: dict) -> None:
        capability_id = data.get("capability_id")
        framework_id = data.get("framework_id")
        if (
            capability_id is not None
            and self.capability_repository.get(capability_id) is None
        ):
            raise InvalidReferenceError(
                f"Capability with id={capability_id} does not exist."
            )
        if (
            framework_id is not None
            and self.framework_repository.get(framework_id) is None
        ):
            raise InvalidReferenceError(
                f"Framework with id={framework_id} does not exist."
            )

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        capability_id = data.get("capability_id")
        framework_id = data.get("framework_id")
        control_id = data.get("control_id")
        if capability_id is None or framework_id is None or control_id is None:
            return
        existing = self.repository.get_by_natural_key(
            capability_id, framework_id, control_id
        )
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "FrameworkMapping",
                f"capability_id={capability_id}, framework_id={framework_id}, "
                f"control_id={control_id!r}",
            )
