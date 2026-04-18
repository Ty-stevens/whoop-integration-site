from app.models.facts import SleepModel
from app.repositories.base import ImportedFactRepository


class SleepRepository(ImportedFactRepository):
    model = SleepModel
    lookup_field = "external_id"

