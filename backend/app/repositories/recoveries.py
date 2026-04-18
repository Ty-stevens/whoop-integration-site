from app.models.facts import RecoveryModel
from app.repositories.base import ImportedFactRepository


class RecoveryRepository(ImportedFactRepository):
    model = RecoveryModel
    lookup_field = "cycle_id"

