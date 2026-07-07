from sqlmodel import Session

from app.models.simulation_run import SimulationRun
from app.repositories.base import BaseRepository


class SimulationRunRepository(BaseRepository[SimulationRun]):
    def __init__(self, session: Session):
        super().__init__(session, SimulationRun)
