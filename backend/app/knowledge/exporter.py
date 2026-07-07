from typing import List

import yaml

from app.models.capability import Capability
from app.models.domain import Domain
from app.models.product_capability_mapping import ProductCapabilityMapping


def dump_domains_yaml(domains: List[Domain]) -> str:
    records = [
        {"name": d.name, "description": d.description}
        for d in sorted(domains, key=lambda d: d.name)
    ]
    return yaml.safe_dump(records, sort_keys=False, allow_unicode=True)


def dump_capabilities_yaml(capabilities: List[Capability]) -> str:
    records = [
        {
            "name": c.name,
            "code": c.code,
            "domain": c.domain.name,
            "description": c.description,
            "risk_category": c.risk_category,
            "is_business_critical": c.is_business_critical,
        }
        for c in sorted(capabilities, key=lambda c: c.code)
    ]
    return yaml.safe_dump(records, sort_keys=False, allow_unicode=True)


def dump_product_mappings_yaml(mappings: List[ProductCapabilityMapping]) -> str:
    records = [
        {
            "vendor": m.vendor.name,
            "product": m.product.name,
            "edition": m.edition.name,
            "module": m.module.name,
            "capability_code": m.capability.code,
            "licensing_tier": m.licensing_tier,
            "supported_platforms": m.supported_platforms,
            "deployment_model": m.deployment_model,
            "availability_status": m.availability_status,
        }
        for m in sorted(
            mappings,
            key=lambda m: (m.vendor.name, m.product.name, m.module.name, m.capability.code),
        )
    ]
    return yaml.safe_dump(records, sort_keys=False, allow_unicode=True)
