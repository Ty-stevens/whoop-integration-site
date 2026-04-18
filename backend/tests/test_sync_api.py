import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.api.routes import sync as sync_routes
from app.db.session import SessionLocal
from app.models.overlays import SyncRunModel
from app.repositories.sync import SyncRepository
from app.services.whoop.provider_client import WhoopCollectionPage
from app.services.whoop.provider_models import (
    WhoopRecoveryCollectionResponse,
    WhoopSleepCollectionResponse,
    WhoopWorkoutCollectionResponse,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "whoop"


class FakeProviderClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def fetch_workouts(self, *, start, end, limit):
        self.calls.append({"resource": "workouts", "start": start, "end": end, "limit": limit})
        payload = load_fixture("workout_collection_scored.json")
        return [
            WhoopCollectionPage(
                raw_payload=payload,
                parsed=WhoopWorkoutCollectionResponse.model_validate(payload),
            )
        ]

    def fetch_sleeps(self, *, start, end, limit):
        self.calls.append({"resource": "sleeps", "start": start, "end": end, "limit": limit})
        payload = load_fixture("sleep_collection_scored.json")
        return [
            WhoopCollectionPage(
                raw_payload=payload,
                parsed=WhoopSleepCollectionResponse.model_validate(payload),
            )
        ]

    def fetch_recoveries(self, *, start, end, limit):
        self.calls.append({"resource": "recoveries", "start": start, "end": end, "limit": limit})
        payload = load_fixture("recovery_collection_scored.json")
        return [
            WhoopCollectionPage(
                raw_payload=payload,
                parsed=WhoopRecoveryCollectionResponse.model_validate(payload),
            )
        ]


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text())


def test_sync_status_returns_idle_defaults(client):
    response = client.get("/api/v1/sync/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "idle"
    assert payload["latest_run"] is None
    assert payload["last_success_at_utc"] is None
    assert payload["counts"] == {"inserted": 0, "updated": 0, "unchanged": 0, "failed": 0}


def test_sync_status_reports_latest_run_and_last_success(client):
    finished_at = datetime(2026, 4, 14, 12, tzinfo=UTC)
    with SessionLocal() as db:
        repo = SyncRepository(db)
        run = repo.create_run(trigger="manual", resource_type="workouts")
        repo.finish_run(run, status="success", inserted_count=1)
        repo.upsert_state(
            resource_type="workouts",
            last_successful_sync_at_utc=finished_at,
            last_window_start_utc=finished_at,
            last_window_end_utc=finished_at,
        )

    response = client.get("/api/v1/sync/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["last_success_at_utc"].startswith("2026-04-14T12:00:00")
    assert payload["latest_run"]["status"] == "success"
    assert payload["latest_run"]["inserted_count"] == 1
    assert payload["counts"] == {"inserted": 1, "updated": 0, "unchanged": 0, "failed": 0}


def test_sync_status_reports_running_when_run_is_active(client):
    with SessionLocal() as db:
        SyncRepository(db).create_run(trigger="manual", resource_type="workouts")

    response = client.get("/api/v1/sync/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["latest_run"]["status"] == "running"


def test_sync_run_rejects_when_running(client):
    with SessionLocal() as db:
        SyncRepository(db).create_run(trigger="manual", resource_type="workouts")

    response = client.post("/api/v1/sync/run", json={"resource_type": "workouts"})

    assert response.status_code == 409


def test_sync_run_for_one_resource_invokes_orchestrator_and_returns_counts(client):
    fake = FakeProviderClient()
    sync_routes.get_sync_provider_client = lambda: fake

    try:
        response = client.post("/api/v1/sync/run", json={"resource_type": "workouts"})
    finally:
        sync_routes.get_sync_provider_client = lambda: None

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["counts"]["inserted"] == 1
    assert [outcome["resource_type"] for outcome in payload["outcomes"]] == ["workouts"]
    assert [call["resource"] for call in fake.calls] == ["workouts"]


def test_sync_run_for_all_resources_returns_per_resource_outcomes(client):
    fake = FakeProviderClient()
    sync_routes.get_sync_provider_client = lambda: fake

    try:
        response = client.post("/api/v1/sync/run", json={})
    finally:
        sync_routes.get_sync_provider_client = lambda: None

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["counts"]["inserted"] == 3
    assert [outcome["resource_type"] for outcome in payload["outcomes"]] == [
        "workouts",
        "sleeps",
        "recoveries",
    ]
    assert [call["resource"] for call in fake.calls] == ["workouts", "sleeps", "recoveries"]


def test_sync_route_response_is_token_and_raw_payload_safe(client):
    fake = FakeProviderClient()
    sync_routes.get_sync_provider_client = lambda: fake

    try:
        response = client.post("/api/v1/sync/run", json={"resource_type": "workouts"})
    finally:
        sync_routes.get_sync_provider_client = lambda: None

    assert response.status_code == 200
    body = response.text
    assert "access_token" not in body
    assert "refresh_token" not in body
    assert "client-secret" not in body
    assert "synthetic_future_field" not in body
    assert "11111111-1111-4111-8111-111111111111" not in body


def test_status_prefers_running_over_latest_finished_run(client):
    with SessionLocal() as db:
        repo = SyncRepository(db)
        running = repo.create_run(trigger="manual", resource_type="workouts")
        finished = SyncRunModel(trigger="manual", resource_type="sleeps", status="success")
        db.add(finished)
        db.commit()
        assert running.id < finished.id

    response = client.get("/api/v1/sync/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert payload["latest_run"]["resource_type"] == "workouts"
