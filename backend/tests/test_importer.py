import textwrap
from pathlib import Path

import pytest
from sqlmodel import select

from app.knowledge.exceptions import (
    DuplicateInBatchError,
    ReferenceNotFoundError,
    YAMLValidationError,
)
from app.knowledge.importer import KnowledgeImporter
from app.models import Vendor


def _write(directory: Path, filename: str, content: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(textwrap.dedent(content).strip() + "\n")


def _build_valid_kb(root: Path) -> None:
    _write(
        root / "vendors",
        "v.yaml",
        """
        name: Acme
        website: https://acme.example
        description: Test vendor.
        headquarters: Testville
        """,
    )
    _write(
        root / "products",
        "p.yaml",
        """
        name: Shield
        vendor: Acme
        category: Endpoint
        description: Test product.
        """,
    )
    _write(
        root / "editions",
        "e.yaml",
        """
        name: Pro
        vendor: Acme
        product: Shield
        tier: Pro
        description: Test edition.
        """,
    )
    _write(
        root / "modules",
        "m.yaml",
        """
        name: Detector
        vendor: Acme
        product: Shield
        edition: Pro
        description: Test module.
        capabilities:
          - EDR-100
        """,
    )
    _write(
        root / "domains",
        "d.yaml",
        """
        name: Endpoint
        description: Test domain.
        """,
    )
    _write(
        root / "capabilities",
        "c.yaml",
        """
        name: Detection
        code: EDR-100
        domain: Endpoint
        description: Test capability.
        risk_category: Detection
        """,
    )
    _write(
        root / "frameworks",
        "f.yaml",
        """
        name: TestFramework
        version: "1.0"
        """,
    )
    _write(
        root / "mappings",
        "map.yaml",
        """
        capability_code: EDR-100
        framework: TestFramework
        framework_version: "1.0"
        control_id: TC-1
        control_name: Test control.
        """,
    )
    _write(
        root / "product_mappings",
        "pm.yaml",
        """
        vendor: Acme
        product: Shield
        edition: Pro
        module: Detector
        capability_code: EDR-100
        licensing_tier: Enterprise
        supported_platforms: [Windows, Cloud]
        deployment_model: Agent
        availability_status: Generally Available
        """,
    )


def test_import_all_creates_expected_rows(session, tmp_path):
    _build_valid_kb(tmp_path)
    result = KnowledgeImporter(session).import_all(tmp_path)

    assert result.vendors.created == 1
    assert result.products.created == 1
    assert result.editions.created == 1
    assert result.modules.created == 1
    assert result.domains.created == 1
    assert result.capabilities.created == 1
    assert result.frameworks.created == 1
    assert result.mappings.created == 1
    assert result.module_capability_links.updated == 1
    assert result.product_capability_mappings.created == 1

    vendor = session.exec(select(Vendor)).one()
    assert vendor.name == "Acme"
    assert len(vendor.products) == 1
    module = vendor.products[0].editions[0].modules[0]
    assert [c.code for c in module.capabilities] == ["EDR-100"]
    assert module.capabilities[0].domain.name == "Endpoint"
    assert module.capabilities[0].framework_mappings[0].control_id == "TC-1"


def test_import_all_is_idempotent(session, tmp_path):
    _build_valid_kb(tmp_path)
    importer = KnowledgeImporter(session)
    importer.import_all(tmp_path)

    result = importer.import_all(tmp_path)

    assert result.vendors.created == 0
    assert result.vendors.unchanged == 1
    assert result.mappings.created == 0
    assert result.mappings.unchanged == 1
    assert len(session.exec(select(Vendor)).all()) == 1


def test_import_updates_changed_fields(session, tmp_path):
    _build_valid_kb(tmp_path)
    importer = KnowledgeImporter(session)
    importer.import_all(tmp_path)

    _write(
        tmp_path / "vendors",
        "v.yaml",
        """
        name: Acme
        website: https://acme.example
        description: Updated description.
        headquarters: Testville
        """,
    )
    result = importer.import_all(tmp_path)

    assert result.vendors.updated == 1
    vendor = session.exec(select(Vendor)).one()
    assert vendor.description == "Updated description."


def test_dry_run_does_not_commit(session, tmp_path):
    _build_valid_kb(tmp_path)
    KnowledgeImporter(session).import_all(tmp_path, dry_run=True)
    assert session.exec(select(Vendor)).all() == []


def test_import_rejects_missing_vendor_reference(session, tmp_path):
    _write(
        tmp_path / "products",
        "p.yaml",
        """
        name: Orphan
        vendor: DoesNotExist
        category: Endpoint
        """,
    )
    with pytest.raises(ReferenceNotFoundError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_missing_capability_reference(session, tmp_path):
    _build_valid_kb(tmp_path)
    _write(
        tmp_path / "modules",
        "m.yaml",
        """
        name: Detector
        vendor: Acme
        product: Shield
        edition: Pro
        description: Test module.
        capabilities:
          - DOES-NOT-EXIST
        """,
    )
    with pytest.raises(ReferenceNotFoundError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_missing_domain_reference(session, tmp_path):
    _write(
        tmp_path / "capabilities",
        "c.yaml",
        """
        name: Detection
        code: EDR-100
        domain: DoesNotExist
        """,
    )
    with pytest.raises(ReferenceNotFoundError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_duplicate_vendor_in_batch(session, tmp_path):
    _write(tmp_path / "vendors", "a.yaml", "name: Acme\n")
    _write(tmp_path / "vendors", "b.yaml", "name: Acme\n")
    with pytest.raises(DuplicateInBatchError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_duplicate_domain_in_batch(session, tmp_path):
    _write(tmp_path / "domains", "a.yaml", "name: Endpoint\n")
    _write(tmp_path / "domains", "b.yaml", "name: Endpoint\n")
    with pytest.raises(DuplicateInBatchError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_missing_module_reference_for_product_mapping(session, tmp_path):
    _build_valid_kb(tmp_path)
    _write(
        tmp_path / "product_mappings",
        "pm2.yaml",
        """
        vendor: Acme
        product: Shield
        edition: Pro
        module: DoesNotExist
        capability_code: EDR-100
        deployment_model: Agent
        """,
    )
    with pytest.raises(ReferenceNotFoundError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_duplicate_product_mapping_in_batch(session, tmp_path):
    _build_valid_kb(tmp_path)
    _write(
        tmp_path / "product_mappings",
        "pm_dup.yaml",
        """
        vendor: Acme
        product: Shield
        edition: Pro
        module: Detector
        capability_code: EDR-100
        licensing_tier: Enterprise
        deployment_model: Agent
        """,
    )
    with pytest.raises(DuplicateInBatchError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_import_rejects_missing_mandatory_field(session, tmp_path):
    _write(tmp_path / "vendors", "v.yaml", "website: https://example.com\n")
    with pytest.raises(YAMLValidationError):
        KnowledgeImporter(session).import_all(tmp_path)


def test_sample_knowledge_base_imports_cleanly(session):
    backend_root = Path(__file__).resolve().parent.parent
    sample_path = backend_root / "app" / "knowledge"
    result = KnowledgeImporter(session).import_all(sample_path)

    assert result.vendors.created == 7
    assert result.products.created == 7
    assert result.editions.created == 7
    assert result.modules.created == 7
    assert result.domains.created == 18
    assert result.capabilities.created == 324
    assert result.frameworks.created == 1
    assert result.mappings.created == 2
    assert result.product_capability_mappings.created == 16
