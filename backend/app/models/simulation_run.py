from typing import Optional

from sqlmodel import Field, SQLModel

from app.models.base import TimestampMixin


class SimulationRunBase(SQLModel):
    scenario_type: str = Field(max_length=50)
    name: Optional[str] = Field(default=None, max_length=255)
    request_json: str
    report_json: str


class SimulationRun(SimulationRunBase, TimestampMixin, table=True):
    """A persisted record of one Simulation Engine run.

    Simulating a scenario never writes to the real assessment data (see
    ``app/engine/simulation_engine.py`` — every mutation happens inside a
    transaction that is always rolled back). This table stores nothing
    about the assessment itself, only the computed, already-final
    ``SimulationReport`` output (as JSON) so a past "what-if" exploration
    can be revisited by id later, the same way a saved report would be.
    """

    __tablename__ = "simulation_run"

    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_project_id: int = Field(
        foreign_key="assessment_project.id", nullable=False, index=True
    )
