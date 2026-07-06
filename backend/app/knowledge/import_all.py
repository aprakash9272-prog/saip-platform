"""CLI entry point for importing the security knowledge base.

Usage:
    python -m app.knowledge.import_all
    python -m app.knowledge.import_all --path /custom/knowledge --dry-run
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from sqlmodel import Session

from app.core.logging import configure_logging
from app.db.session import engine
from app.knowledge.exceptions import KnowledgeImportError
from app.knowledge.importer import KnowledgeImporter

configure_logging()
logger = logging.getLogger(__name__)

DEFAULT_KNOWLEDGE_PATH = Path(__file__).resolve().parent


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Import the SAIP security knowledge base from YAML."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_KNOWLEDGE_PATH,
        help=(
            "Knowledge base root directory containing vendors/, products/, "
            "editions/, modules/, capabilities/, frameworks/, mappings/ "
            "(default: app/knowledge)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the batch and report what would happen without committing.",
    )
    args = parser.parse_args(argv)

    with Session(engine) as session:
        importer = KnowledgeImporter(session)
        try:
            result = importer.import_all(args.path, dry_run=args.dry_run)
        except KnowledgeImportError as exc:
            logger.error("Knowledge base import failed: %s", exc)
            return 1

    for name, summary in result.as_dict().items():
        logger.info(
            "%-24s created=%-4d updated=%-4d unchanged=%-4d",
            name,
            summary.created,
            summary.updated,
            summary.unchanged,
        )

    if args.dry_run:
        logger.info("Dry run complete — no changes were committed.")
    else:
        logger.info("Knowledge base import complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
