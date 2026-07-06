import pytest
from pydantic import ValidationError

from app.knowledge.exceptions import CircularReferenceError
from app.knowledge.graph import check_for_cycles
from app.knowledge.yaml_schemas import CapabilityYAML, ModuleYAML, VendorYAML


def test_vendor_yaml_requires_name():
    with pytest.raises(ValidationError):
        VendorYAML.model_validate({"website": "https://example.com"})


def test_vendor_yaml_accepts_minimal_payload():
    vendor = VendorYAML.model_validate({"name": "Acme"})
    assert vendor.name == "Acme"
    assert vendor.website is None


def test_module_yaml_requires_hierarchy_fields():
    with pytest.raises(ValidationError):
        ModuleYAML.model_validate({"name": "Detector"})


def test_module_yaml_defaults_capabilities_to_empty_list():
    module = ModuleYAML.model_validate(
        {"name": "Detector", "vendor": "Acme", "product": "Shield", "edition": "Pro"}
    )
    assert module.capabilities == []


def test_capability_code_rejects_invalid_characters():
    with pytest.raises(ValidationError):
        CapabilityYAML.model_validate({"name": "Detection", "code": "bad code!"})


def test_capability_code_accepts_slug_like_value():
    capability = CapabilityYAML.model_validate({"name": "Detection", "code": "EDR-001"})
    assert capability.code == "EDR-001"


def test_check_for_cycles_passes_on_acyclic_graph():
    check_for_cycles({"a": ["b"], "b": ["c"], "c": []})


def test_check_for_cycles_detects_direct_cycle():
    with pytest.raises(CircularReferenceError):
        check_for_cycles({"a": ["b"], "b": ["a"]})


def test_check_for_cycles_detects_indirect_cycle():
    with pytest.raises(CircularReferenceError) as exc_info:
        check_for_cycles({"a": ["b"], "b": ["c"], "c": ["a"]})
    assert exc_info.value.cycle[0] == exc_info.value.cycle[-1]
