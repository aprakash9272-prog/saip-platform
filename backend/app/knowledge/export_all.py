"""CLI entry point for exporting the security knowledge base to YAML.

Usage:
    python -m app.knowledge.export_all
    python -m app.knowledge.export_all --path /custom/output/dir
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from sqlmodel import Session

from app.core.logging import configure_logging
from app.db.session import engine
from app.knowledge.exporter import (
    dump_capabilities_yaml,
    dump_domains_yaml,
    dump_product_mappings_yaml,
)
from app.repositories.capability import CapabilityRepository
from app.repositories.domain import DomainRepository
from app.repositories.product_capability_mapping import ProductCapabilityMappingRepository

configure_logging()
logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = Path(__file__).resolve().parent.parent.parent / "exports" / "knowledge"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export the SAIP security knowledge base to YAML."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=(
            "Output directory; writes domains/_export.yaml, "
            "capabilities/_export.yaml, and product_mappings/_export.yaml "
            "(default: backend/exports/knowledge — deliberately outside "
            "app/knowledge/ so re-running `import_all` against the source "
            "tree never sees duplicate records)."
        ),
    )
    args = parser.parse_args(argv)

    with Session(engine) as session:
        domains = DomainRepository(session).list(skip=0, limit=1_000_000)[0]
        capabilities = CapabilityRepository(session).all()
        product_mappings = ProductCapabilityMappingRepository(session).all()

        domains_dir = args.path / "domains"
        capabilities_dir = args.path / "capabilities"
        product_mappings_dir = args.path / "product_mappings"
        domains_dir.mkdir(parents=True, exist_ok=True)
        capabilities_dir.mkdir(parents=True, exist_ok=True)
        product_mappings_dir.mkdir(parents=True, exist_ok=True)

        (domains_dir / "_export.yaml").write_text(dump_domains_yaml(domains))
        (capabilities_dir / "_export.yaml").write_text(
            dump_capabilities_yaml(capabilities)
        )
        (product_mappings_dir / "_export.yaml").write_text(
            dump_product_mappings_yaml(product_mappings)
        )

    logger.info(
        "Exported %d domains, %d capabilities, and %d product mappings to %s",
        len(domains),
        len(capabilities),
        len(product_mappings),
        args.path,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
