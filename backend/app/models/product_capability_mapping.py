from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.capability import Capability
    from app.models.edition import Edition
    from app.models.module import Module
    from app.models.product import Product
    from app.models.vendor import Vendor


class DeploymentModel(str, Enum):
    AGENT = "Agent"
    SAAS = "SaaS"
    NETWORK = "Network"
    HYBRID = "Hybrid"


class AvailabilityStatus(str, Enum):
    GENERALLY_AVAILABLE = "Generally Available"
    BETA = "Beta"
    PREVIEW = "Preview"
    DEPRECATED = "Deprecated"
    DISCONTINUED = "Discontinued"


class Platform(str, Enum):
    WINDOWS = "Windows"
    MACOS = "macOS"
    LINUX = "Linux"
    CLOUD = "Cloud"
    MOBILE = "Mobile"


class ProductCapabilityMappingBase(SQLModel):
    licensing_tier: Optional[str] = Field(default=None, max_length=100)
    supported_platforms: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    deployment_model: str = Field(max_length=50)
    availability_status: str = Field(
        default=AvailabilityStatus.GENERALLY_AVAILABLE.value, max_length=50
    )


class ProductCapabilityMapping(ProductCapabilityMappingBase, TimestampMixin, table=True):
    """The core mapping layer: which capability a vendor's module provides,
    under what license tier, on which platforms, via which deployment model.

    vendor_id/product_id/edition_id are denormalized alongside module_id
    (which alone determines the rest of the hierarchy) so this — the fact
    table future coverage/gap/overlap engines will query — never needs a
    deep join just to filter by vendor or product.
    """

    __tablename__ = "product_capability_mapping"
    __table_args__ = (
        UniqueConstraint(
            "module_id",
            "capability_id",
            "licensing_tier",
            "deployment_model",
            name="uq_product_mapping_module_capability_tier_deployment",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="vendor.id", nullable=False, index=True)
    product_id: int = Field(foreign_key="product.id", nullable=False, index=True)
    edition_id: int = Field(foreign_key="edition.id", nullable=False, index=True)
    module_id: int = Field(foreign_key="module.id", nullable=False, index=True)
    capability_id: int = Field(foreign_key="capability.id", nullable=False, index=True)

    vendor: "Vendor" = Relationship()
    product: "Product" = Relationship()
    edition: "Edition" = Relationship()
    module: "Module" = Relationship()
    capability: "Capability" = Relationship()
