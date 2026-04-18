from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.overlays import SyncRunModel, SyncStateModel


class SyncRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        *,
        trigger: str,
        resource_type: str | None = None,
        window_start_utc: datetime | None = None,
        window_end_utc: datetime | None = None,
    ) -> SyncRunModel:
        row = SyncRunModel(
            trigger=trigger,
            resource_type=resource_type,
            status="running",
            window_start_utc=window_start_utc,
            window_end_utc=window_end_utc,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def finish_run(
        self,
        run: SyncRunModel,
        *,
        status: str,
        inserted_count: int = 0,
        updated_count: int = 0,
        unchanged_count: int = 0,
        failed_count: int = 0,
        error_message: str | None = None,
    ) -> SyncRunModel:
        run.status = status
        run.inserted_count = inserted_count
        run.updated_count = updated_count
        run.unchanged_count = unchanged_count
        run.failed_count = failed_count
        run.error_message = error_message
        run.finished_at_utc = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(run)
        return run

    def upsert_state(
        self,
        *,
        resource_type: str,
        last_successful_sync_at_utc: datetime | None,
        last_window_start_utc: datetime | None,
        last_window_end_utc: datetime | None,
        cursor_text: str | None = None,
    ) -> SyncStateModel:
        row = (
            self.db.query(SyncStateModel)
            .filter(SyncStateModel.resource_type == resource_type)
            .one_or_none()
        )
        if row is None:
            row = SyncStateModel(resource_type=resource_type)
            self.db.add(row)
        row.last_successful_sync_at_utc = last_successful_sync_at_utc
        row.last_window_start_utc = last_window_start_utc
        row.last_window_end_utc = last_window_end_utc
        row.cursor_text = cursor_text
        row.updated_at_utc = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_state(self, resource_type: str) -> SyncStateModel | None:
        return (
            self.db.query(SyncStateModel)
            .filter(SyncStateModel.resource_type == resource_type)
            .one_or_none()
        )

    def get_states(self) -> list[SyncStateModel]:
        return self.db.query(SyncStateModel).order_by(SyncStateModel.resource_type.asc()).all()

    def get_latest_run(self) -> SyncRunModel | None:
        return self.db.query(SyncRunModel).order_by(SyncRunModel.id.desc()).first()

    def get_latest_running_run(self) -> SyncRunModel | None:
        return (
            self.db.query(SyncRunModel)
            .filter(SyncRunModel.status == "running")
            .order_by(SyncRunModel.id.desc())
            .first()
        )
