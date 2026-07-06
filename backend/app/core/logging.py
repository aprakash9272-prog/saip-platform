import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure root logging for the application."""

    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(settings.LOG_LEVEL)
