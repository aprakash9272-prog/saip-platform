from typing import List

from pydantic import BaseModel


class RefItem(BaseModel):
    id: int
    name: str


class CapabilityRefItem(BaseModel):
    id: int
    code: str
    name: str


class FrameworkRefItem(BaseModel):
    id: int
    name: str
    version: str


class AssessmentDashboard(BaseModel):
    """Informational rollup for an assessment project. No scoring, no gap
    analysis — just counts and the underlying entities, for the future
    Coverage/Gap/Overlap engines to build on."""

    total_deployed_products: int
    distinct_product_count: int
    vendor_count: int
    vendors: List[RefItem]
    module_count: int
    modules: List[RefItem]
    capability_count: int
    capabilities: List[CapabilityRefItem]
    domain_count: int
    domains: List[RefItem]
    framework_count: int
    frameworks: List[FrameworkRefItem]
