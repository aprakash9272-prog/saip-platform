from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, or_
from sqlmodel import Session, SQLModel, select

ModelType = TypeVar("ModelType", bound=SQLModel)


class BaseRepository(Generic[ModelType]):
    """Generic data-access layer shared by every knowledge base entity."""

    search_fields: Sequence[str] = ()

    def __init__(self, session: Session, model: Type[ModelType]):
        self.session = session
        self.model = model

    def get(self, id_: int) -> Optional[ModelType]:
        return self.session.get(self.model, id_)

    def get_by(self, **filters: Any) -> Optional[ModelType]:
        statement = select(self.model)
        for field, value in filters.items():
            statement = statement.where(getattr(self.model, field) == value)
        return self.session.exec(statement).first()

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        filters: Optional[dict] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
    ) -> tuple[list[ModelType], int]:
        statement = select(self.model)
        count_statement = select(func.count()).select_from(self.model)

        if search and self.search_fields:
            conditions = [
                getattr(self.model, field).ilike(f"%{search}%")
                for field in self.search_fields
            ]
            statement = statement.where(or_(*conditions))
            count_statement = count_statement.where(or_(*conditions))

        for field, value in (filters or {}).items():
            if value is None:
                continue
            condition = getattr(self.model, field) == value
            statement = statement.where(condition)
            count_statement = count_statement.where(condition)

        total = self.session.exec(count_statement).one()

        order_column = self.model.id
        if sort_by and hasattr(self.model, sort_by):
            order_column = getattr(self.model, sort_by)
        order_clause = order_column.desc() if sort_desc else order_column.asc()

        items = self.session.exec(
            statement.offset(skip).limit(limit).order_by(order_clause)
        ).all()
        return list(items), total

    def distinct_values(self, field: str) -> list:
        column = getattr(self.model, field)
        statement = (
            select(column).where(column.is_not(None)).distinct().order_by(column)
        )
        return list(self.session.exec(statement).all())

    def create(self, obj: ModelType) -> ModelType:
        self.session.add(obj)
        self.session.commit()
        self.session.refresh(obj)
        return obj

    def update(self, db_obj: ModelType, data: dict) -> ModelType:
        for field, value in data.items():
            setattr(db_obj, field, value)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: ModelType) -> None:
        self.session.delete(db_obj)
        self.session.commit()
