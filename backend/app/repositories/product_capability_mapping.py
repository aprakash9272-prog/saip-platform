from typing import List, Optional

from sqlmodel import Session

from app.models.product_capability_mapping import ProductCapabilityMapping
from app.repositories.base import BaseRepository


class ProductCapabilityMappingRepository(BaseRepository[ProductCapabilityMapping]):
    search_fields = ("licensing_tier", "deployment_model", "availability_status")

    def __init__(self, session: Session):
        super().__init__(session, ProductCapabilityMapping)

    def get_by_natural_key(
        self,
        module_id: int,
        capability_id: int,
        licensing_tier: Optional[str],
        deployment_model: str,
    ) -> Optional[ProductCapabilityMapping]:
        return self.get_by(
            module_id=module_id,
            capability_id=capability_id,
            licensing_tier=licensing_tier,
            deployment_model=deployment_model,
        )

    def list_deployment_models(self) -> List[str]:
        return self.distinct_values("deployment_model")

    def list_availability_statuses(self) -> List[str]:
        return self.distinct_values("availability_status")

    def list_licensing_tiers(self) -> List[str]:
        return self.distinct_values("licensing_tier")

    def all(self) -> List[ProductCapabilityMapping]:
        items, _ = self.list(skip=0, limit=1_000_000)
        return items

    def get_many(self, ids: List[int]) -> List[ProductCapabilityMapping]:
        return [obj for obj in (self.get(id_) for id_ in ids) if obj is not None]
