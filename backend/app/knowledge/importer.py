from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, ValidationError
from sqlmodel import Session

from app.knowledge.exceptions import (
    DuplicateInBatchError,
    ReferenceNotFoundError,
    YAMLValidationError,
)
from app.knowledge.graph import check_for_cycles
from app.knowledge.loader import load_yaml_directory
from app.knowledge.yaml_schemas import (
    CapabilityYAML,
    EditionYAML,
    FrameworkMappingYAML,
    FrameworkYAML,
    ModuleYAML,
    ProductYAML,
    VendorYAML,
)
from app.models.capability import Capability
from app.models.edition import Edition
from app.models.framework import Framework
from app.models.framework_mapping import FrameworkMapping
from app.models.module import Module
from app.models.product import Product
from app.models.vendor import Vendor
from app.repositories.capability import CapabilityRepository
from app.repositories.edition import EditionRepository
from app.repositories.framework import FrameworkRepository
from app.repositories.framework_mapping import FrameworkMappingRepository
from app.repositories.module import ModuleRepository
from app.repositories.product import ProductRepository
from app.repositories.vendor import VendorRepository

Record = Tuple[str, Any]


@dataclass
class ImportSummary:
    created: int = 0
    updated: int = 0
    unchanged: int = 0

    def record(self, status: str) -> None:
        setattr(self, status, getattr(self, status) + 1)

    @property
    def total(self) -> int:
        return self.created + self.updated + self.unchanged


@dataclass
class ImportResult:
    vendors: ImportSummary = field(default_factory=ImportSummary)
    products: ImportSummary = field(default_factory=ImportSummary)
    editions: ImportSummary = field(default_factory=ImportSummary)
    modules: ImportSummary = field(default_factory=ImportSummary)
    module_capability_links: ImportSummary = field(default_factory=ImportSummary)
    capabilities: ImportSummary = field(default_factory=ImportSummary)
    frameworks: ImportSummary = field(default_factory=ImportSummary)
    mappings: ImportSummary = field(default_factory=ImportSummary)

    def as_dict(self) -> Dict[str, ImportSummary]:
        return {
            "vendors": self.vendors,
            "products": self.products,
            "editions": self.editions,
            "modules": self.modules,
            "module_capability_links": self.module_capability_links,
            "capabilities": self.capabilities,
            "frameworks": self.frameworks,
            "mappings": self.mappings,
        }


class KnowledgeImporter:
    """Validates and imports the YAML security knowledge base.

    Import order is fixed: Vendor, Product, Edition, Module, Capability,
    Framework, Mapping. Module -> Capability links are many-to-many and are
    declared on the Module record (a module lists the capability codes it
    provides); since Capability is imported *after* Module, those links are
    queued during the Module step and resolved once Capability rows exist.
    """

    def __init__(self, session: Session):
        self.session = session
        self.vendor_repo = VendorRepository(session)
        self.product_repo = ProductRepository(session)
        self.edition_repo = EditionRepository(session)
        self.module_repo = ModuleRepository(session)
        self.capability_repo = CapabilityRepository(session)
        self.framework_repo = FrameworkRepository(session)
        self.mapping_repo = FrameworkMappingRepository(session)

    def import_all(self, base_path: Path, dry_run: bool = False) -> ImportResult:
        raw_vendors = load_yaml_directory(base_path / "vendors")
        raw_products = load_yaml_directory(base_path / "products")
        raw_editions = load_yaml_directory(base_path / "editions")
        raw_modules = load_yaml_directory(base_path / "modules")
        raw_capabilities = load_yaml_directory(base_path / "capabilities")
        raw_frameworks = load_yaml_directory(base_path / "frameworks")
        raw_mappings = load_yaml_directory(base_path / "mappings")

        vendors = self._validate_batch(raw_vendors, VendorYAML)
        products = self._validate_batch(raw_products, ProductYAML)
        editions = self._validate_batch(raw_editions, EditionYAML)
        modules = self._validate_batch(raw_modules, ModuleYAML)
        capabilities = self._validate_batch(raw_capabilities, CapabilityYAML)
        frameworks = self._validate_batch(raw_frameworks, FrameworkYAML)
        mappings = self._validate_batch(raw_mappings, FrameworkMappingYAML)

        self._check_batch_duplicates(vendors, key=lambda v: v.name, entity="Vendor")
        self._check_batch_duplicates(
            products, key=lambda p: (p.vendor, p.name), entity="Product"
        )
        self._check_batch_duplicates(
            editions,
            key=lambda e: (e.vendor, e.product, e.name),
            entity="Edition",
        )
        self._check_batch_duplicates(
            modules,
            key=lambda m: (m.vendor, m.product, m.edition, m.name),
            entity="Module",
        )
        self._check_batch_duplicates(
            capabilities, key=lambda c: c.code, entity="Capability"
        )
        self._check_batch_duplicates(
            frameworks, key=lambda f: (f.name, f.version), entity="Framework"
        )
        self._check_batch_duplicates(
            mappings,
            key=lambda m: (
                m.capability_code,
                m.framework,
                m.framework_version,
                m.control_id,
            ),
            entity="FrameworkMapping",
        )

        check_for_cycles(
            self._build_dependency_graph(products, editions, modules, mappings)
        )

        result = ImportResult()

        vendor_by_name: Dict[str, Vendor] = {}
        for source, data in vendors:
            obj, status_ = self._upsert(Vendor, self.vendor_repo.get_by_name(data.name), data.model_dump())
            vendor_by_name[data.name] = obj
            result.vendors.record(status_)

        product_by_key: Dict[Tuple[str, str], Product] = {}
        for source, data in products:
            vendor = vendor_by_name.get(data.vendor) or self.vendor_repo.get_by_name(
                data.vendor
            )
            if vendor is None:
                raise ReferenceNotFoundError(
                    f"{source}: product '{data.name}' references unknown "
                    f"vendor '{data.vendor}'"
                )
            payload = data.model_dump(exclude={"vendor"})
            payload["vendor_id"] = vendor.id
            existing = self.product_repo.get_by_vendor_and_name(vendor.id, data.name)
            obj, status_ = self._upsert(Product, existing, payload)
            product_by_key[(data.vendor, data.name)] = obj
            result.products.record(status_)

        edition_by_key: Dict[Tuple[str, str, str], Edition] = {}
        for source, data in editions:
            product = product_by_key.get(
                (data.vendor, data.product)
            ) or self._find_product(data.vendor, data.product)
            if product is None:
                raise ReferenceNotFoundError(
                    f"{source}: edition '{data.name}' references unknown product "
                    f"'{data.product}' (vendor '{data.vendor}')"
                )
            payload = data.model_dump(exclude={"vendor", "product"})
            payload["product_id"] = product.id
            existing = self.edition_repo.get_by_product_and_name(
                product.id, data.name
            )
            obj, status_ = self._upsert(Edition, existing, payload)
            edition_by_key[(data.vendor, data.product, data.name)] = obj
            result.editions.record(status_)

        module_by_key: Dict[Tuple[str, str, str, str], Module] = {}
        pending_links: List[Tuple[Module, List[str], str]] = []
        for source, data in modules:
            edition = edition_by_key.get(
                (data.vendor, data.product, data.edition)
            ) or self._find_edition(data.vendor, data.product, data.edition)
            if edition is None:
                raise ReferenceNotFoundError(
                    f"{source}: module '{data.name}' references unknown edition "
                    f"'{data.edition}' (product '{data.product}', vendor "
                    f"'{data.vendor}')"
                )
            payload = data.model_dump(
                exclude={"vendor", "product", "edition", "capabilities"}
            )
            payload["edition_id"] = edition.id
            existing = self.module_repo.get_by_edition_and_name(
                edition.id, data.name
            )
            obj, status_ = self._upsert(Module, existing, payload)
            module_by_key[(data.vendor, data.product, data.edition, data.name)] = obj
            pending_links.append((obj, data.capabilities, source))
            result.modules.record(status_)

        capability_by_code: Dict[str, Capability] = {}
        for source, data in capabilities:
            existing = self.capability_repo.get_by_code(data.code)
            obj, status_ = self._upsert(Capability, existing, data.model_dump())
            capability_by_code[data.code] = obj
            result.capabilities.record(status_)

        for module_obj, codes, source in pending_links:
            resolved: List[Capability] = []
            for code in codes:
                capability = capability_by_code.get(
                    code
                ) or self.capability_repo.get_by_code(code)
                if capability is None:
                    raise ReferenceNotFoundError(
                        f"{source}: module '{module_obj.name}' references unknown "
                        f"capability code '{code}'"
                    )
                resolved.append(capability)
            existing_ids = sorted(c.id for c in module_obj.capabilities)
            new_ids = sorted(c.id for c in resolved)
            if existing_ids != new_ids:
                module_obj.capabilities = resolved
                self.session.add(module_obj)
                self.session.flush()
                result.module_capability_links.record("updated")
            else:
                result.module_capability_links.record("unchanged")

        framework_by_key: Dict[Tuple[str, str], Framework] = {}
        for source, data in frameworks:
            existing = self.framework_repo.get_by_name_version(
                data.name, data.version
            )
            obj, status_ = self._upsert(Framework, existing, data.model_dump())
            framework_by_key[(data.name, data.version)] = obj
            result.frameworks.record(status_)

        for source, data in mappings:
            capability = capability_by_code.get(
                data.capability_code
            ) or self.capability_repo.get_by_code(data.capability_code)
            if capability is None:
                raise ReferenceNotFoundError(
                    f"{source}: mapping references unknown capability code "
                    f"'{data.capability_code}'"
                )
            framework = framework_by_key.get(
                (data.framework, data.framework_version)
            ) or self.framework_repo.get_by_name_version(
                data.framework, data.framework_version
            )
            if framework is None:
                raise ReferenceNotFoundError(
                    f"{source}: mapping references unknown framework "
                    f"'{data.framework}' version '{data.framework_version}'"
                )
            existing = self.mapping_repo.get_by_natural_key(
                capability.id, framework.id, data.control_id
            )
            payload = {
                "capability_id": capability.id,
                "framework_id": framework.id,
                "control_id": data.control_id,
                "control_name": data.control_name,
            }
            obj, status_ = self._upsert(FrameworkMapping, existing, payload)
            result.mappings.record(status_)

        if dry_run:
            self.session.rollback()
        else:
            self.session.commit()

        return result

    # -- helpers ---------------------------------------------------------

    def _validate_batch(
        self, records: List[Record], schema_cls: Type[BaseModel]
    ) -> List[Tuple[str, Any]]:
        parsed = []
        for source, raw in records:
            try:
                parsed.append((source, schema_cls.model_validate(raw)))
            except ValidationError as exc:
                raise YAMLValidationError(source, str(exc)) from exc
        return parsed

    def _check_batch_duplicates(
        self,
        records: List[Tuple[str, Any]],
        *,
        key: Callable[[Any], Any],
        entity: str,
    ) -> None:
        seen: Dict[Any, str] = {}
        for source, record in records:
            record_key = key(record)
            if record_key in seen:
                raise DuplicateInBatchError(
                    entity, str(record_key), [seen[record_key], source]
                )
            seen[record_key] = source

    def _build_dependency_graph(
        self,
        products: List[Tuple[str, ProductYAML]],
        editions: List[Tuple[str, EditionYAML]],
        modules: List[Tuple[str, ModuleYAML]],
        mappings: List[Tuple[str, FrameworkMappingYAML]],
    ) -> Dict[str, List[str]]:
        edges: Dict[str, List[str]] = {}

        def add_edge(child: str, parent: str) -> None:
            edges.setdefault(child, []).append(parent)
            edges.setdefault(parent, [])

        for _, p in products:
            add_edge(f"product:{p.vendor}/{p.name}", f"vendor:{p.vendor}")
        for _, e in editions:
            add_edge(
                f"edition:{e.vendor}/{e.product}/{e.name}",
                f"product:{e.vendor}/{e.product}",
            )
        for _, m in modules:
            module_key = f"module:{m.vendor}/{m.product}/{m.edition}/{m.name}"
            add_edge(module_key, f"edition:{m.vendor}/{m.product}/{m.edition}")
            for code in m.capabilities:
                add_edge(module_key, f"capability:{code}")
        for _, mp in mappings:
            mapping_key = (
                f"mapping:{mp.capability_code}/{mp.framework}/"
                f"{mp.framework_version}/{mp.control_id}"
            )
            add_edge(mapping_key, f"capability:{mp.capability_code}")
            add_edge(mapping_key, f"framework:{mp.framework}/{mp.framework_version}")

        return edges

    def _find_product(self, vendor_name: str, product_name: str) -> Optional[Product]:
        vendor = self.vendor_repo.get_by_name(vendor_name)
        if vendor is None:
            return None
        return self.product_repo.get_by_vendor_and_name(vendor.id, product_name)

    def _find_edition(
        self, vendor_name: str, product_name: str, edition_name: str
    ) -> Optional[Edition]:
        product = self._find_product(vendor_name, product_name)
        if product is None:
            return None
        return self.edition_repo.get_by_product_and_name(product.id, edition_name)

    def _upsert(self, model_cls: type, existing: Any, payload: dict) -> Tuple[Any, str]:
        if existing is not None:
            changed = any(getattr(existing, k) != v for k, v in payload.items())
            if changed:
                for k, v in payload.items():
                    setattr(existing, k, v)
                self.session.add(existing)
                self.session.flush()
                return existing, "updated"
            return existing, "unchanged"

        obj = model_cls(**payload)
        self.session.add(obj)
        self.session.flush()
        return obj, "created"
