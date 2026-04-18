from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.time import ensure_utc


@dataclass(frozen=True)
class UpsertResult:
    row: Any
    inserted: bool = False
    updated: bool = False
    unchanged: bool = False


class ImportedFactRepository:
    model: type
    lookup_field: str

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_lookup(self, value: str):
        return (
            self.db.query(self.model)
            .filter(getattr(self.model, self.lookup_field) == value)
            .one_or_none()
        )

    def upsert(self, values: dict[str, Any]) -> UpsertResult:
        lookup_value = values[self.lookup_field]
        row = self.get_by_lookup(lookup_value)
        if row is None:
            row = self.model(**values)
            self.db.add(row)
            self.db.commit()
            self.db.refresh(row)
            return UpsertResult(row=row, inserted=True)

        if self._should_update(row, values):
            # P6 transformers provide canonical fact dictionaries here.
            # Manual overlays live in separate tables and must never be touched by this update.
            next_revision = row.source_revision + 1
            for key, value in values.items():
                if key == "source_revision":
                    continue
                setattr(row, key, value)
            row.source_revision = next_revision
            self.db.commit()
            self.db.refresh(row)
            return UpsertResult(row=row, updated=True)

        return UpsertResult(row=row, unchanged=True)

    def list_by_iso_week(self, week_start) -> list:
        return (
            self.db.query(self.model)
            .filter(self.model.iso_week_start_date == week_start)
            .order_by(self.model.id.asc())
            .all()
        )

    def list_by_month(self, month_start) -> list:
        return (
            self.db.query(self.model)
            .filter(self.model.local_month_start_date == month_start)
            .order_by(self.model.id.asc())
            .all()
        )

    def _should_update(self, row, values: dict[str, Any]) -> bool:
        incoming_hash = values.get("payload_hash")
        if incoming_hash and incoming_hash != row.payload_hash:
            return True

        incoming_updated_at = values.get("external_updated_at_utc")
        existing_updated_at = row.external_updated_at_utc
        if incoming_updated_at is None or existing_updated_at is None:
            return False

        return ensure_utc(incoming_updated_at) > ensure_utc(existing_updated_at)


def count_results(results: Iterable[UpsertResult]) -> dict[str, int]:
    counts = {"inserted": 0, "updated": 0, "unchanged": 0}
    for result in results:
        if result.inserted:
            counts["inserted"] += 1
        elif result.updated:
            counts["updated"] += 1
        elif result.unchanged:
            counts["unchanged"] += 1
    return counts
