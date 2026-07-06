from typing import List


class KnowledgeImportError(Exception):
    """Base error for knowledge base import failures."""


class YAMLValidationError(KnowledgeImportError):
    def __init__(self, source: str, errors: str):
        self.source = source
        super().__init__(f"{source}: {errors}")


class DuplicateInBatchError(KnowledgeImportError):
    def __init__(self, entity: str, key: str, sources: List[str]):
        super().__init__(
            f"Duplicate {entity} '{key}' defined in: {', '.join(sources)}"
        )


class ReferenceNotFoundError(KnowledgeImportError):
    pass


class CircularReferenceError(KnowledgeImportError):
    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        super().__init__(f"Circular reference detected: {' -> '.join(cycle)}")
