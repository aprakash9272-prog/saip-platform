import time

from app.engine.recommendation_engine import RecommendationEngine
from tests.test_gap_performance import CAPABILITIES_PER_DOMAIN, DOMAIN_COUNT, _seed_bulk_catalog


def test_recommendation_engine_completes_quickly_at_scale(session):
    project_id = _seed_bulk_catalog(session)

    start = time.perf_counter()
    report = RecommendationEngine(session).calculate(project_id)
    elapsed = time.perf_counter() - start

    assert report.total_gaps > 0
    assert report.addressable_gaps > 0
    # Half the vendors in the seeded catalog are undeployed, so their slice
    # of capabilities should be addressable gaps with real candidates.
    assert len(report.recommendations) == report.addressable_gaps
    assert len(report.product_comparison) > 0
    total_from_matrix = sum(entry.count for entry in report.priority_matrix)
    assert total_from_matrix == len(report.recommendations)
    assert report.total_gaps == report.addressable_gaps + report.unaddressable_gaps
    # Sanity: never exceeds the full 360-capability catalog.
    assert report.total_gaps <= DOMAIN_COUNT * CAPABILITIES_PER_DOMAIN
    # Generous threshold — this is a regression guard against accidental
    # N+1 queries, not a strict benchmark.
    assert elapsed < 5.0, f"RecommendationEngine.calculate took too long: {elapsed:.2f}s"
