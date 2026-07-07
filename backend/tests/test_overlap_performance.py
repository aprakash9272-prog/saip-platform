import time

from app.engine.overlap_engine import OverlapEngine
from tests.test_gap_performance import DOMAIN_COUNT, CAPABILITIES_PER_DOMAIN, _seed_bulk_catalog


def test_overlap_engine_completes_quickly_at_scale(session):
    project_id = _seed_bulk_catalog(session)

    start = time.perf_counter()
    report = OverlapEngine(session).calculate(project_id)
    elapsed = time.perf_counter() - start

    assert report.total_deployed_products > 0
    assert report.total_vendors > 0
    assert len(report.vendor_summary) == report.total_vendors
    assert len(report.domain_overlap_scores) == DOMAIN_COUNT
    assert report.duplicate_capability_count <= DOMAIN_COUNT * CAPABILITIES_PER_DOMAIN
    for score in (
        report.optimization_score,
        report.vendor_consolidation_score,
        report.cost_optimization_score,
        report.operational_complexity_score,
    ):
        assert 0.0 <= score <= 100.0
    # Generous threshold — this is a regression guard against accidental
    # N+1 queries or unbounded pairwise blowups, not a strict benchmark.
    assert elapsed < 5.0, f"OverlapEngine.calculate took too long: {elapsed:.2f}s"
