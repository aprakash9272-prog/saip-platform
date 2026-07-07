from typing import Optional

from sqlmodel import Session

from app.core.exceptions import DuplicateEntityError, InvalidReferenceError
from app.models.assessment_project import AssessmentProject
from app.models.product_assignment import ProductAssignment
from app.repositories.assessment_project import AssessmentProjectRepository
from app.repositories.customer import CustomerRepository
from app.repositories.edition import EditionRepository
from app.repositories.environment import EnvironmentRepository
from app.repositories.module import ModuleRepository
from app.repositories.product import ProductRepository
from app.repositories.product_assignment import ProductAssignmentRepository
from app.repositories.vendor import VendorRepository
from app.schemas.assessment_export import (
    AssessmentImportResult,
    AssessmentProjectExport,
    ProductAssignmentExport,
)
from app.schemas.dashboard import (
    AssessmentDashboard,
    CapabilityRefItem,
    FrameworkRefItem,
    RefItem,
)
from app.services.base import BaseService


class AssessmentProjectService(BaseService[AssessmentProject]):
    entity_name = "AssessmentProject"

    def __init__(self, session: Session):
        super().__init__(AssessmentProjectRepository(session))
        self.session = session
        self.customer_repository = CustomerRepository(session)
        self.assignment_repository = ProductAssignmentRepository(session)

    def validate_references(self, data: dict) -> None:
        customer_id = data.get("customer_id")
        if customer_id is not None and self.customer_repository.get(customer_id) is None:
            raise InvalidReferenceError(f"Customer with id={customer_id} does not exist.")

    def validate_duplicate(self, data: dict, exclude_id: Optional[int] = None) -> None:
        customer_id = data.get("customer_id")
        name = data.get("name")
        if customer_id is None or name is None:
            return
        existing = self.repository.get_by_customer_and_name(customer_id, name)
        if existing and existing.id != exclude_id:
            raise DuplicateEntityError(
                "AssessmentProject", f"customer_id={customer_id}, name={name!r}"
            )

    # -- dashboard ---------------------------------------------------------

    def dashboard(self, project_id: int) -> AssessmentDashboard:
        """Informational rollup only — no coverage/gap/overlap scoring."""
        self.get(project_id)
        assignments = self.assignment_repository.list_by_assessment_project(project_id)

        vendors: dict[int, str] = {}
        products: set[int] = set()
        modules: dict[int, str] = {}
        capabilities: dict[int, CapabilityRefItem] = {}
        domains: dict[int, str] = {}
        frameworks: dict[int, FrameworkRefItem] = {}

        for assignment in assignments:
            vendors[assignment.vendor_id] = assignment.vendor.name
            products.add(assignment.product_id)
            for module in assignment.modules:
                modules[module.id] = module.name
                for capability in module.capabilities:
                    capabilities[capability.id] = CapabilityRefItem(
                        id=capability.id, code=capability.code, name=capability.name
                    )
                    domains[capability.domain_id] = capability.domain.name
                    for mapping in capability.framework_mappings:
                        frameworks[mapping.framework_id] = FrameworkRefItem(
                            id=mapping.framework.id,
                            name=mapping.framework.name,
                            version=mapping.framework.version,
                        )

        return AssessmentDashboard(
            total_deployed_products=len(assignments),
            distinct_product_count=len(products),
            vendor_count=len(vendors),
            vendors=[
                RefItem(id=k, name=v)
                for k, v in sorted(vendors.items(), key=lambda kv: kv[1])
            ],
            module_count=len(modules),
            modules=[
                RefItem(id=k, name=v)
                for k, v in sorted(modules.items(), key=lambda kv: kv[1])
            ],
            capability_count=len(capabilities),
            capabilities=sorted(capabilities.values(), key=lambda c: c.code),
            domain_count=len(domains),
            domains=[
                RefItem(id=k, name=v)
                for k, v in sorted(domains.items(), key=lambda kv: kv[1])
            ],
            framework_count=len(frameworks),
            frameworks=sorted(frameworks.values(), key=lambda f: (f.name, f.version)),
        )

    # -- export / import ----------------------------------------------------

    def export(self, project_id: int) -> AssessmentProjectExport:
        project = self.get(project_id)
        assignments = self.assignment_repository.list_by_assessment_project(project_id)
        return AssessmentProjectExport(
            customer=project.customer.name,
            name=project.name,
            description=project.description,
            status=project.status,
            start_date=project.start_date,
            target_completion_date=project.target_completion_date,
            assignments=[
                ProductAssignmentExport(
                    vendor=a.vendor.name,
                    product=a.product.name,
                    edition=a.edition.name,
                    modules=sorted(m.name for m in a.modules),
                    environment=a.environment.name,
                    license_quantity=a.license_quantity,
                    deployment_model=a.deployment_model,
                    deployment_status=a.deployment_status,
                    notes=a.notes,
                )
                for a in assignments
            ],
        )

    def import_payload(self, payload: AssessmentProjectExport) -> AssessmentImportResult:
        customer = self.customer_repository.get_by_name(payload.customer)
        if customer is None:
            raise InvalidReferenceError(f"Customer '{payload.customer}' does not exist.")

        project_data = {
            "customer_id": customer.id,
            "name": payload.name,
            "description": payload.description,
            "status": payload.status,
            "start_date": payload.start_date,
            "target_completion_date": payload.target_completion_date,
        }
        existing_project = self.repository.get_by_customer_and_name(
            customer.id, payload.name
        )
        if existing_project:
            changed = any(
                getattr(existing_project, key) != value
                for key, value in project_data.items()
            )
            if changed:
                for key, value in project_data.items():
                    setattr(existing_project, key, value)
                self.session.add(existing_project)
                self.session.flush()
                project_status = "updated"
            else:
                project_status = "unchanged"
            project = existing_project
        else:
            project = AssessmentProject(**project_data)
            self.session.add(project)
            self.session.flush()
            project_status = "created"

        vendor_repo = VendorRepository(self.session)
        product_repo = ProductRepository(self.session)
        edition_repo = EditionRepository(self.session)
        module_repo = ModuleRepository(self.session)
        environment_repo = EnvironmentRepository(self.session)

        created = updated = unchanged = 0

        for item in payload.assignments:
            vendor = vendor_repo.get_by_name(item.vendor)
            if vendor is None:
                raise InvalidReferenceError(f"Vendor '{item.vendor}' does not exist.")
            product = product_repo.get_by_vendor_and_name(vendor.id, item.product)
            if product is None:
                raise InvalidReferenceError(
                    f"Product '{item.product}' does not exist for vendor '{item.vendor}'."
                )
            edition = edition_repo.get_by_product_and_name(product.id, item.edition)
            if edition is None:
                raise InvalidReferenceError(
                    f"Edition '{item.edition}' does not exist for product '{item.product}'."
                )
            environment = environment_repo.get_by_customer_and_name(
                customer.id, item.environment
            )
            if environment is None:
                raise InvalidReferenceError(
                    f"Environment '{item.environment}' does not exist for "
                    f"customer '{payload.customer}'."
                )

            modules = []
            for module_name in item.modules:
                module = module_repo.get_by_edition_and_name(edition.id, module_name)
                if module is None:
                    raise InvalidReferenceError(
                        f"Module '{module_name}' does not exist for edition '{item.edition}'."
                    )
                modules.append(module)

            assignment_data = {
                "assessment_project_id": project.id,
                "vendor_id": vendor.id,
                "product_id": product.id,
                "edition_id": edition.id,
                "environment_id": environment.id,
                "license_quantity": item.license_quantity,
                "deployment_model": item.deployment_model,
                "deployment_status": item.deployment_status,
                "notes": item.notes,
            }

            existing_assignment = self.assignment_repository.get_by_natural_key(
                project.id, edition.id, environment.id
            )
            if existing_assignment:
                changed = any(
                    getattr(existing_assignment, key) != value
                    for key, value in assignment_data.items()
                )
                existing_module_ids = sorted(m.id for m in existing_assignment.modules)
                new_module_ids = sorted(m.id for m in modules)
                if changed or existing_module_ids != new_module_ids:
                    for key, value in assignment_data.items():
                        setattr(existing_assignment, key, value)
                    existing_assignment.modules = modules
                    self.session.add(existing_assignment)
                    self.session.flush()
                    updated += 1
                else:
                    unchanged += 1
            else:
                new_assignment = ProductAssignment(**assignment_data)
                new_assignment.modules = modules
                self.session.add(new_assignment)
                self.session.flush()
                created += 1

        self.session.commit()

        return AssessmentImportResult(
            project_id=project.id,
            project_status=project_status,
            assignments_created=created,
            assignments_updated=updated,
            assignments_unchanged=unchanged,
        )
