from pathlib import Path
from typing import Any, List, Tuple

import yaml

from app.knowledge.exceptions import KnowledgeImportError


def load_yaml_directory(directory: Path) -> List[Tuple[str, Any]]:
    """Load every *.yml/*.yaml file in `directory` into (source, record) pairs.

    A file may contain a single mapping or a list of mappings. `source` is the
    file path, carried through validation and import so errors can point back
    to the offending file.
    """
    if not directory.exists():
        return []

    records: List[Tuple[str, Any]] = []
    for path in sorted(directory.glob("*.yml")) + sorted(directory.glob("*.yaml")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise KnowledgeImportError(f"{path}: invalid YAML — {exc}") from exc

        if data is None:
            continue
        if isinstance(data, list):
            for item in data:
                records.append((str(path), item))
        elif isinstance(data, dict):
            records.append((str(path), data))
        else:
            raise KnowledgeImportError(
                f"{path}: expected a mapping or a list of mappings, "
                f"got {type(data).__name__}"
            )
    return records
