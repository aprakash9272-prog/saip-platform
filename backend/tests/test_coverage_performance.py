import time

from app.engine.coverage_engine import CoverageEngine
from app.models.assessment_project import AssessmentProject
from app.models.capability import Capability
from app.models.customer import Customer
from app.models.domain import Domain
from app.models.edition import Edition
from app.models.environment import Environment
from app.models.module import Module
from app.models.product import Product
from app.models.product_assignment import ProductAssignment
from app.models.vendor import Vendor

DOMAIN_COUNT = 18
CAPABILITIES_PER_DOMAIN = 20  # 360 total, comparable to the real ~324-capability catalog
VENDOR_COUNT = 10
ASSIGNMENT_COUNT = 60  # 6 assignments per vendor across 6 editions/modules


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
                )
            )
    session.add_all(capabilities)
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

        # Each vendor's module covers a distinct slice of capabilities so
        # there is real work for the engine to dedupe/aggregate, plus some
        # deliberate overlap with the previous vendor to exercise duplicate
        # detection under load.
        start = (v_index * 15) % len(capabilities)
        slice_ = capabilities[start : start + 30] or capabilities[:30]
        module = Module(name=f"Module {v_index}", edition_id=edition.id)
        module.capabilities = slice_
        session.add(module)
        session.flush()

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
            # Each assignment needs its own edition/environment pair to
            # satisfy the uniqueness constraint, so vary the environment.
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


def test_coverage_engine_completes_quickly_at_scale(session):
    project_id = _seed_bulk_catalog(session)

    start = time.perf_counter()
    report = CoverageEngine(session).calculate(project_id)
    elapsed = time.perf_counter() - start

    assert report.total_capabilities == DOMAIN_COUNT * CAPABILITIES_PER_DOMAIN
    assert report.covered_capability_count > 0
    # Generous threshold — this is a regression guard against accidental
    # N+1 queries, not a strict benchmark.
    assert elapsed < 5.0, f"CoverageEngine.calculate took too long: {elapsed:.2f}s"
