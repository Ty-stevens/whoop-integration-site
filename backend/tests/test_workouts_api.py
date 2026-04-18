from app.db.session import SessionLocal
from app.models.facts import WorkoutModel
from app.repositories.annotations import AnnotationRepository
from tests.fact_fixtures import workout_values


def create_workout(db, **overrides) -> WorkoutModel:
    row = WorkoutModel(**workout_values(**overrides))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def test_recent_workouts_returns_annotations_without_raw_payloads(client):
    with SessionLocal() as db:
        workout = create_workout(db)
        AnnotationRepository(db).upsert_workout_annotation(
            workout.id,
            manual_classification="strength",
            manual_strength_split="upper",
            tag="gym",
            notes="Bench day",
        )

    response = client.get("/api/v1/workouts/recent")

    assert response.status_code == 200
    payload = response.json()
    assert payload["workouts"][0]["effective_classification"] == "strength"
    assert payload["workouts"][0]["annotation"]["manual_strength_split"] == "upper"
    assert "raw_payload_json" not in response.text
    assert "access_token" not in response.text


def test_patch_workout_annotation_creates_updates_and_clears(client):
    with SessionLocal() as db:
        workout = create_workout(db)

    response = client.patch(
        f"/api/v1/workouts/{workout.id}/annotation",
        json={
            "manual_classification": "strength",
            "manual_strength_split": "full",
            "tag": "  race prep  ",
            "notes": "  hard lift  ",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["manual_classification"] == "strength"
    assert payload["manual_strength_split"] == "full"
    assert payload["tag"] == "race prep"
    assert payload["notes"] == "hard lift"

    response = client.patch(
        f"/api/v1/workouts/{workout.id}/annotation",
        json={
            "manual_classification": None,
            "manual_strength_split": None,
            "tag": "",
            "notes": " ",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["manual_classification"] is None
    assert payload["manual_strength_split"] is None
    assert payload["tag"] is None
    assert payload["notes"] is None


def test_patch_workout_annotation_validates_and_404s(client):
    missing = client.patch("/api/v1/workouts/999/annotation", json={})
    invalid = client.patch(
        "/api/v1/workouts/999/annotation",
        json={"manual_strength_split": "push"},
    )

    assert missing.status_code == 404
    assert invalid.status_code == 422


def test_strength_overview_counts_tagged_and_untagged_strength(client):
    with SessionLocal() as db:
        strength = create_workout(db)
        strength.classification = "strength"
        strength.strain = 7.5
        db.commit()
        manual_strength = create_workout(
            db,
            external_id="workout-2",
            payload_hash="hash-2",
            raw_payload_json={"id": "workout-2"},
        )
        AnnotationRepository(db).upsert_workout_annotation(
            manual_strength.id,
            manual_classification="strength",
            manual_strength_split="lower",
        )

    response = client.get("/api/v1/workouts/strength-overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["strength_sessions"] == 2
    assert payload["untagged_sessions"] == 1
    assert payload["weekly_counts"][0]["count"] == 2
    assert payload["monthly_counts"][0]["count"] == 2
    lower = next(item for item in payload["split_counts"] if item["split"] == "lower")
    assert lower["count"] == 1
