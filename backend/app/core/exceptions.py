from typing import Any


class SAIPError(Exception):
    """Base class for domain-level errors raised by the service layer."""


class EntityNotFoundError(SAIPError):
    def __init__(self, entity: str, identifier: Any):
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} with id={identifier!r} was not found.")


class DuplicateEntityError(SAIPError):
    def __init__(self, entity: str, detail: str):
        self.entity = entity
        self.detail = detail
        super().__init__(f"{entity} already exists: {detail}")


class InvalidReferenceError(SAIPError):
    def __init__(self, message: str):
        super().__init__(message)
