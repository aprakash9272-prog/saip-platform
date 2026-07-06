from typing import List

import yaml

from app.models.capability import Capability
from app.models.domain import Domain


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
        }
        for c in sorted(capabilities, key=lambda c: c.code)
    ]
    return yaml.safe_dump(records, sort_keys=False, allow_unicode=True)
