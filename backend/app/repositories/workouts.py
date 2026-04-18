from app.models.facts import WorkoutModel
from app.repositories.base import ImportedFactRepository


class WorkoutRepository(ImportedFactRepository):
    model = WorkoutModel
    lookup_field = "external_id"

