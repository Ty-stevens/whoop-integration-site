import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from app.core.time import ensure_utc
from app.db.session import SessionLocal
from app.models.facts import WorkoutModel
from app.models.overlays import SyncRunModel
from app.repositories.sync import SyncRepository
from app.services.sync.orchestrator import SyncOrchestrator
from app.services.whoop.provider_client import WhoopCollectionPage
from app.services.whoop.provider_models import (
    WhoopRecoveryCollectionResponse,
    WhoopSleepCollectionResponse,
    WhoopWorkoutCollectionResponse,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "whoop"
NOW = datetime(2026, 4, 14, 12, tzinfo=UTC)


class FakeProviderClient:
    def __init__(
        self,
        *,
        workout_pages: list[WhoopCollectionPage] | None = None,
        sleep_pages: list[WhoopCollectionPage] | None = None,
        recovery_pages: list[WhoopCollectionPage] | None = None,
        fail_resource: str | None = None,
    ) -> None:
        self.workout_pages = workout_pages or []
        self.sleep_pages = sleep_pages or []
        self.recovery_pages = recovery_pages or []
        self.fail_resource = fail_resource
        self.calls: list[dict[str, Any]] = []

    def fetch_workouts(self, *, start, end, limit):
        self.calls.append({"resource": "workouts", "start": start, "end": end, "limit": limit})
        if self.fail_resource == "workouts":
            raise RuntimeError("provider failed with access-token raw payload")
        return self.workout_pages

    def fetch_sleeps(self, *, start, end, limit):
        self.calls.append({"resource": "sleeps", "start": start, "end": end, "limit": limit})
        if self.fail_resource == "sleeps":
            raise RuntimeError("provider failed")
        return self.sleep_pages

    def fetch_recoveries(self, *, start, end, limit):
        self.calls.append({"resource": "recoveries", "start": start, "end": end, "limit": limit})
        if self.fail_resource == "recoveries":
            raise RuntimeError("provider failed")
        return self.recovery_pages


class FlakyWorkoutRepository:
    calls = 0

    def __init__(self, db) -> None:
        self.db = db

    def upsert(self, values):
        from app.models.facts import WorkoutModel
        from app.repositories.workouts import WorkoutRepository

        type(self).calls += 1
        if type(self).calls == 1:
            self.db.add(WorkoutModel(**values))
            self.db.flush()
            raise RuntimeError("simulated repository failure after flush")
        return WorkoutRepository(self.db).upsert(values)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def workout_page(payload: dict | None = None) -> WhoopCollectionPage:
    payload = payload or load_fixture("workout_collection_scored.json")
    return WhoopCollectionPage(
        raw_payload=payload,
        parsed=WhoopWorkoutCollectionResponse.model_validate(payload),
    )


def sleep_page(payload: dict | None = None) -> WhoopCollectionPage:
    payload = payload or load_fixture("sleep_collection_scored.json")
    return WhoopCollectionPage(
        raw_payload=payload,
        parsed=WhoopSleepCollectionResponse.model_validate(payload),
    )


def recovery_page(payload: dict | None = None) -> WhoopCollectionPage:
    payload = payload or load_fixture("recovery_collection_scored.json")
    return WhoopCollectionPage(
        raw_payload=payload,
        parsed=WhoopRecoveryCollectionResponse.model_validate(payload),
    )


def test_initial_backfill_uses_180_day_window_and_updates_sync_state():
    fake = FakeProviderClient(workout_pages=[workout_page()])

    with SessionLocal() as db:
        outcome = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="initial_backfill",
        )
        state = SyncRepository(db).get_state("workouts")
        run = db.get(SyncRunModel, outcome.run_id)

    assert fake.calls[0]["start"] == NOW - timedelta(days=180)
    assert fake.calls[0]["end"] == NOW
    assert fake.calls[0]["limit"] == 25
    assert outcome.status == "success"
    assert outcome.counts.inserted == 1
    assert state is not None
    assert ensure_utc(state.last_successful_sync_at_utc) == NOW
    assert ensure_utc(state.last_window_start_utc) == NOW - timedelta(days=180)
    assert ensure_utc(state.last_window_end_utc) == NOW
    assert state.cursor_text is None
    assert run is not None
    assert ensure_utc(run.window_start_utc) == NOW - timedelta(days=180)
    assert ensure_utc(run.window_end_utc) == NOW


def test_incremental_sync_uses_three_day_overlap_from_previous_window_end():
    previous_end = datetime(2026, 4, 10, 12, tzinfo=UTC)
    fake = FakeProviderClient(workout_pages=[workout_page()])

    with SessionLocal() as db:
        SyncRepository(db).upsert_state(
            resource_type="workouts",
            last_successful_sync_at_utc=previous_end,
            last_window_start_utc=previous_end - timedelta(days=7),
            last_window_end_utc=previous_end,
            cursor_text="old-cursor",
        )
        outcome = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="manual",
        )

    assert outcome.status == "success"
    assert fake.calls[0]["start"] == previous_end - timedelta(days=3)
    assert fake.calls[0]["end"] == NOW


def test_each_resource_sync_fetches_transforms_and_inserts_rows():
    fake = FakeProviderClient(
        workout_pages=[workout_page()],
        sleep_pages=[sleep_page()],
        recovery_pages=[recovery_page()],
    )

    with SessionLocal() as db:
        outcomes = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_all(
            trigger="initial_backfill"
        )

    assert [outcome.resource_type for outcome in outcomes] == ["workouts", "sleeps", "recoveries"]
    assert [outcome.status for outcome in outcomes] == ["success", "success", "success"]
    assert [outcome.counts.inserted for outcome in outcomes] == [1, 1, 1]
    assert [call["resource"] for call in fake.calls] == ["workouts", "sleeps", "recoveries"]


def test_repeated_sync_of_same_payload_counts_unchanged_on_second_run():
    fake = FakeProviderClient(workout_pages=[workout_page()])

    with SessionLocal() as db:
        orchestrator = SyncOrchestrator(db, fake, clock=lambda: NOW)
        first = orchestrator.sync_resource(resource_type="workouts", trigger="manual")
        second = orchestrator.sync_resource(resource_type="workouts", trigger="manual")

    assert first.counts.inserted == 1
    assert second.counts.unchanged == 1


def test_changed_payload_hash_updates_row_and_increments_source_revision():
    original = load_fixture("workout_collection_scored.json")
    changed = load_fixture("workout_collection_scored.json")
    changed["records"][0]["synthetic_future_field"] = "changed"

    with SessionLocal() as db:
        SyncOrchestrator(
            db,
            FakeProviderClient(workout_pages=[workout_page(original)]),
            clock=lambda: NOW,
        ).sync_resource(resource_type="workouts", trigger="manual")
        outcome = SyncOrchestrator(
            db,
            FakeProviderClient(workout_pages=[workout_page(changed)]),
            clock=lambda: NOW,
        ).sync_resource(resource_type="workouts", trigger="manual")
        workout = db.query(WorkoutModel).one()

    assert outcome.counts.updated == 1
    assert workout.source_revision == 2
    assert workout.raw_payload_json["synthetic_future_field"] == "changed"


def test_provider_fetch_failure_marks_run_failed_and_does_not_advance_state():
    fake = FakeProviderClient(fail_resource="workouts")

    with SessionLocal() as db:
        outcome = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="manual",
        )
        state = SyncRepository(db).get_state("workouts")
        run = db.get(SyncRunModel, outcome.run_id)

    assert outcome.status == "failed"
    assert outcome.counts.failed == 0
    assert state is None
    assert run is not None
    assert run.status == "failed"
    assert run.error_message is not None
    assert "access-token" not in run.error_message
    assert "raw payload" in run.error_message


def test_single_malformed_record_marks_partial_persists_good_records_and_leaves_state():
    payload = load_fixture("workout_collection_scored.json")
    good_record = payload["records"][0]
    bad_record = {**good_record, "id": "bad-workout", "end": "2022-04-23T01:25:44.774Z"}
    mixed_payload = {"records": [good_record, bad_record]}
    fake = FakeProviderClient(workout_pages=[workout_page(mixed_payload)])

    with SessionLocal() as db:
        outcome = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="manual",
        )
        state = SyncRepository(db).get_state("workouts")
        workout_count = db.query(WorkoutModel).count()
        run = db.get(SyncRunModel, outcome.run_id)

    assert outcome.status == "partial"
    assert outcome.counts.inserted == 1
    assert outcome.counts.failed == 1
    assert state is not None
    assert state.last_successful_sync_at_utc is None
    assert ensure_utc(state.last_window_end_utc) == NOW
    assert workout_count == 1
    assert run is not None
    assert run.status == "partial"
    assert run.failed_count == 1


def test_missing_raw_record_marks_partial_without_upserting_empty_raw_payload():
    payload = load_fixture("workout_collection_scored.json")
    page = workout_page(payload)
    page = WhoopCollectionPage(raw_payload={"records": []}, parsed=page.parsed)
    fake = FakeProviderClient(workout_pages=[page])

    with SessionLocal() as db:
        outcome = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="manual",
        )
        state = SyncRepository(db).get_state("workouts")
        workout_count = db.query(WorkoutModel).count()

    assert outcome.status == "partial"
    assert outcome.counts.failed == 1
    assert state is None
    assert workout_count == 0
    assert outcome.error_message is not None
    assert "raw record is missing" in outcome.error_message


def test_record_failure_rolls_back_session_so_run_can_finish_and_continue(monkeypatch):
    from app.services.sync import orchestrator as orchestrator_module

    payload = load_fixture("workout_collection_scored.json")
    second_record = {**payload["records"][0], "id": "second-workout-id"}
    mixed_payload = {"records": [payload["records"][0], second_record]}
    spec = orchestrator_module.RESOURCE_SPECS["workouts"]
    monkeypatch.setitem(
        orchestrator_module.RESOURCE_SPECS,
        "workouts",
        orchestrator_module.ResourceSyncSpec(
            spec.fetch_method_name,
            FlakyWorkoutRepository,
            spec.transform,
        ),
    )
    FlakyWorkoutRepository.calls = 0

    with SessionLocal() as db:
        outcome = SyncOrchestrator(
            db,
            FakeProviderClient(workout_pages=[workout_page(mixed_payload)]),
            clock=lambda: NOW,
        ).sync_resource(resource_type="workouts", trigger="manual")
        run = db.get(SyncRunModel, outcome.run_id)
        workouts = db.query(WorkoutModel).all()

    assert outcome.status == "partial"
    assert outcome.counts.failed == 1
    assert outcome.counts.inserted == 1
    assert run is not None
    assert run.status == "partial"
    assert [workout.external_id for workout in workouts] == ["second-workout-id"]


def test_successful_sync_clears_prior_cursor_in_sync_state():
    fake = FakeProviderClient(workout_pages=[workout_page()])

    with SessionLocal() as db:
        SyncRepository(db).upsert_state(
            resource_type="workouts",
            last_successful_sync_at_utc=NOW - timedelta(days=1),
            last_window_start_utc=NOW - timedelta(days=8),
            last_window_end_utc=NOW - timedelta(days=1),
            cursor_text="old-cursor",
        )
        SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="scheduled",
        )
        state = SyncRepository(db).get_state("workouts")

    assert state is not None
    assert state.cursor_text is None
    assert ensure_utc(state.last_successful_sync_at_utc) == NOW


def test_partial_error_message_is_token_safe_and_does_not_include_raw_payload_json():
    payload = load_fixture("workout_collection_scored.json")
    payload["records"][0]["end"] = "2022-04-23T01:25:44.774Z"
    fake = FakeProviderClient(workout_pages=[workout_page(payload)])

    with SessionLocal() as db:
        outcome = SyncOrchestrator(db, fake, clock=lambda: NOW).sync_resource(
            resource_type="workouts",
            trigger="manual",
        )
        run = db.get(SyncRunModel, outcome.run_id)

    assert run is not None
    assert run.error_message is not None
    assert "access_token" not in run.error_message
    assert "refresh_token" not in run.error_message
    assert "11111111-1111-4111-8111-111111111111" not in run.error_message
