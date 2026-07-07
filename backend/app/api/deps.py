from typing import Annotated, Optional

from fastapi import Depends, Query
from sqlmodel import Session

from app.db.session import get_session

SessionDep = Annotated[Session, Depends(get_session)]


class PaginationParams:
    """Shared list-endpoint query params: pagination + free-text search."""

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip."),
        limit: int = Query(50, ge=1, le=500, description="Max records to return."),
        search: Optional[str] = Query(
            None, min_length=1, max_length=200, description="Free-text search."
        ),
    ):
        self.skip = skip
        self.limit = limit
        self.search = search
