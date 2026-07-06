from typing import List, Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.capability import Capability
from app.models.module import Module
from app.repositories.capability import CapabilityRepository
from app.repositories.edition import EditionRepository
from app.repositories.module import ModuleRepository
from app.services.base import BaseService


class ModuleService(BaseService[Module]):
    entity_name = "Module"

    def __init__(self, session: Session):
        super().__init__(ModuleRepository(session))
        self.session = session
        self.edition_repository = EditionRepository(session)
        self.capability_repository = CapabilityRepository(session)

    def validate_references(self, data: dict) -> None:
        edition_id = data.get("edition_id")
        if edition_id is not None and self.edition_repository.get(edition_id) is None:
            raise InvalidReferenceError(f"Edition with id={edition_id} does not exist.")

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        edition_id = data.get("edition_id")
        name = data.get("name")
        if edition_id is None or name is None:
            return
        existing = self.repository.get_by_edition_and_name(edition_id, name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "Module", f"edition_id={edition_id}, name={name!r}"
            )

    def _resolve_capabilities(self, capability_ids: List[int]) -> List[Capability]:
        capabilities = []
        for capability_id in capability_ids:
            capability = self.capability_repository.get(capability_id)
            if capability is None:
                raise InvalidReferenceError(
                    f"Capability with id={capability_id} does not exist."
                )
            capabilities.append(capability)
        return capabilities

    def create(self, data: dict) -> Module:
        data = dict(data)
        capability_ids = data.pop("capability_ids", [])
        self.validate_references(data)
        self.validate_duplicate(data)
        obj = Module(**data)
        obj.capabilities = self._resolve_capabilities(capability_ids)
        return self.repository.create(obj)

    def update(self, id_: int, data: dict) -> Module:
        obj = self.get(id_)
        data = dict(data)
        capability_ids = data.pop("capability_ids", None)
        clean = {k: v for k, v in data.items() if v is not None}
        self.validate_references(clean)
        self.validate_duplicate(clean, exclude_id=id_)
        updated = self.repository.update(obj, clean)
        if capability_ids is not None:
            updated.capabilities = self._resolve_capabilities(capability_ids)
            self.session.add(updated)
            self.session.commit()
            self.session.refresh(updated)
        return updated
