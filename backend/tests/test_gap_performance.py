import time

from app.engine.gap_engine import GapEngine
from app.models.assessment_project import AssessmentProject
from app.models.capability import Capability
from app.models.customer import Customer
from app.models.domain import Domain
from app.models.edition import Edition
from app.models.environment import Environment
from app.models.framework import Framework
from app.models.framework_mapping import FrameworkMapping
from app.models.module import Module
from app.models.product import Product
from app.models.product_assignment import ProductAssignment
from app.models.product_capability_mapping import ProductCapabilityMapping
from app.models.vendor import Vendor

DOMAIN_COUNT = 18
CAPABILITIES_PER_DOMAIN = 20  # 360 total, comparable to the real ~324-capability catalog
VENDOR_COUNT = 10
ASSIGNMENT_COUNT = 60
RISK_CATEGORIES = ["Critical", "High", "Medium", "Low", None]


def _seed_bulk_catalog(session):
    domains = [Domain(name=f"Domain {i}") for i in range(DOMAIN_COUNT)]
    session.add_all(domains)
    session.flush()

    capabilities = []
    for d_index, domain in enumerate(domains):
        for c_index in range(CAPABILITIES_PER_DOMAIN):
            capabilities.append(
                Capability(
                    name=f"Capability {d_index}-{c_index}",
                    code=f"CAP-{d_index}-{c_index}",
                    domain_id=domain.id,
                    risk_category=RISK_CATEGORIES[c_index % len(RISK_CATEGORIES)],
                    is_business_critical=(c_index % 7 == 0),
                )
            )
    session.add_all(capabilities)
    session.flush()

    # Give roughly a third of capabilities 1-3 framework controls, so the
    # gap engine has real framework-mapping work to do for missing gaps.
    framework = Framework(name="NIST CSF", version="2.0")
    session.add(framework)
    session.flush()
    for index, capability in enumerate(capabilities):
        if index % 3 == 0:
            for control_index in range(1 + index % 3):
                session.add(
                    FrameworkMapping(
                        capability_id=capability.id,
                        framework_id=framework.id,
                        control_id=f"CTRL-{index}-{control_index}",
                        control_name=f"Control {index}-{control_index}",
                    )
                )
    session.flush()

    customer = Customer(name="Perf Customer")
    session.add(customer)
    session.flush()

    environment = Environment(
        name="Production", environment_type="Production", customer_id=customer.id
    )
    session.add(environment)
    session.flush()

    project = AssessmentProject(name="Perf Assessment", customer_id=customer.id)
    session.add(project)
    session.flush()

    for v_index in range(VENDOR_COUNT):
        vendor = Vendor(name=f"Vendor {v_index}")
        session.add(vendor)
        session.flush()
        product = Product(name=f"Product {v_index}", vendor_id=vendor.id)
        session.add(product)
        session.flush()
        edition = Edition(name=f"Edition {v_index}", product_id=product.id)
        session.add(edition)
        session.flush()

        start = (v_index * 15) % len(capabilities)
        slice_ = capabilities[start : start + 30] or capabilities[:30]
        module = Module(name=f"Module {v_index}", edition_id=edition.id)
        module.capabilities = slice_
        session.add(module)
        session.flush()

        # Catalog mappings exist for every vendor's slice, regardless of
        # whether that vendor ends up deployed below — this is the data the
        # gap engine's "mapped products" lookup scans.
        for capability in slice_:
            session.add(
                ProductCapabilityMapping(
                    vendor_id=vendor.id,
                    product_id=product.id,
                    edition_id=edition.id,
                    module_id=module.id,
                    capability_id=capability.id,
                    deployment_model="Agent",
                )
            )

        # Only deploy half the vendors, so the other half's capabilities
        # remain gaps with candidate catalog products attached.
        if v_index % 2 == 0:
            assignments_for_vendor = ASSIGNMENT_COUNT // VENDOR_COUNT
            for a_index in range(assignments_for_vendor):
                assignment = ProductAssignment(
                    assessment_project_id=project.id,
                    vendor_id=vendor.id,
                    product_id=product.id,
                    edition_id=edition.id,
                    environment_id=environment.id,
                    deployment_model="Agent",
                    deployment_status="Deployed",
                )
                extra_environment = Environment(
                    name=f"Env {v_index}-{a_index}",
                    environment_type="Production",
                    customer_id=customer.id,
                )
                session.add(extra_environment)
                session.flush()
                assignment.environment_id = extra_environment.id
                assignment.modules = [module]
                session.add(assignment)

    session.commit()
    return project.id


def test_gap_engine_completes_quickly_at_scale(session):
    project_id = _seed_bulk_catalog(session)

    start = time.perf_counter()
    report = GapEngine(session).calculate(project_id)
    elapsed = time.perf_counter() - start

    assert report.total_capabilities == DOMAIN_COUNT * CAPABILITIES_PER_DOMAIN
    assert report.total_gaps > 0
    assert len(report.domain_gap_scores) == DOMAIN_COUNT
    # Generous threshold — this is a regression guard against accidental
    # N+1 queries, not a strict benchmark.
    assert elapsed < 5.0, f"GapEngine.calculate took too long: {elapsed:.2f}s"
