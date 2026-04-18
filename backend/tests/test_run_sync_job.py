from datetime import UTC, datetime

from app.jobs import run_sync
from app.services.sync.orchestrator import SyncCounts, SyncOutcome
from app.services.sync.service import SyncAlreadyRunningError

NOW = datetime(2026, 4, 14, 12, tzinfo=UTC)


def outcome(resource_type: str, status: str = "success") -> SyncOutcome:
    return SyncOutcome(
        run_id=1,
        resource_type=resource_type,  # type: ignore[arg-type]
        trigger="scheduled",
        status=status,
        window_start_utc=NOW,
        window_end_utc=NOW,
        counts=SyncCounts(
            inserted=1,
            updated=2,
            unchanged=3,
            failed=4 if status == "partial" else 0,
        ),
        error_message=None,
    )


def test_scheduled_job_runs_one_mocked_resource_and_prints_summary(monkeypatch, capsys):
    calls = []

    def fake_run_scheduled_sync(db, *, resource_type, settings=None, provider_client=None):
        calls.append(resource_type)
        return [outcome(resource_type)]

    monkeypatch.setattr(run_sync, "run_scheduled_sync", fake_run_scheduled_sync)

    exit_code = run_sync.main(["--trigger", "scheduled", "--resource", "workouts"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert calls == ["workouts"]
    assert "Sync scheduled/workouts: success" in output
    assert "inserted=1" in output


def test_job_resource_all_runs_all_resources(monkeypatch, capsys):
    def fake_run_scheduled_sync(db, *, resource_type, settings=None, provider_client=None):
        assert resource_type == "all"
        return [
            outcome("workouts"),
            outcome("sleeps"),
            outcome("recoveries"),
        ]

    monkeypatch.setattr(run_sync, "run_scheduled_sync", fake_run_scheduled_sync)

    exit_code = run_sync.main(["--resource", "all"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Sync scheduled/all: success inserted=3 updated=6 unchanged=9 failed=0" in output


def test_active_running_sync_returns_exit_code_one(monkeypatch, capsys):
    def fake_run_scheduled_sync(db, *, resource_type, settings=None, provider_client=None):
        raise SyncAlreadyRunningError("A sync run is already in progress.")

    monkeypatch.setattr(run_sync, "run_scheduled_sync", fake_run_scheduled_sync)

    exit_code = run_sync.main(["--resource", "all"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "already in progress" in output


def test_failed_sync_returns_exit_code_one(monkeypatch, capsys):
    def fake_run_scheduled_sync(db, *, resource_type, settings=None, provider_client=None):
        return [outcome("workouts", status="failed")]

    monkeypatch.setattr(run_sync, "run_scheduled_sync", fake_run_scheduled_sync)

    exit_code = run_sync.main(["--resource", "workouts"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "failed" in output


def test_partial_sync_returns_zero_and_output_is_token_safe(monkeypatch, capsys):
    def fake_run_scheduled_sync(db, *, resource_type, settings=None, provider_client=None):
        return [outcome("workouts", status="partial")]

    monkeypatch.setattr(run_sync, "run_scheduled_sync", fake_run_scheduled_sync)

    exit_code = run_sync.main(["--resource", "workouts"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "partial" in output
    assert "access_token" not in output
    assert "refresh_token" not in output
    assert "Bearer " not in output
