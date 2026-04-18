import pytest

from app.services.workouts.classification import classify_workout_sport, normalize_sport_name


@pytest.mark.parametrize(
    "sport_name",
    [
        "running",
        "cycling",
        "rowing",
        "swimming",
        "hiking",
        "walking",
        "elliptical",
        "stair climber",
        "treadmill",
        "trail running",
        "indoor cycling",
    ],
)
def test_known_cardio_sports_classify_as_cardio(sport_name):
    assert classify_workout_sport(sport_name) == "cardio"


@pytest.mark.parametrize(
    "sport_name",
    [
        "weightlifting",
        "functional fitness",
        "strength trainer",
        "resistance training",
        "pilates",
        "calisthenics",
    ],
)
def test_known_strength_sports_classify_as_strength(sport_name):
    assert classify_workout_sport(sport_name) == "strength"


@pytest.mark.parametrize("sport_name", [None, "", "  ", "pickleball", "yoga", "sport"])
def test_unknown_or_ambiguous_sports_classify_as_unknown(sport_name):
    assert classify_workout_sport(sport_name) == "unknown"


@pytest.mark.parametrize(
    ("sport_name", "expected"),
    [
        (" Trail-Running ", "cardio"),
        ("INDOOR_CYCLING", "cardio"),
        ("Stair   Climber", "cardio"),
        ("Strength/Trainer", "strength"),
        ("Functional-Fitness!", "strength"),
    ],
)
def test_case_spacing_and_punctuation_variants_classify_consistently(sport_name, expected):
    assert classify_workout_sport(sport_name) == expected


def test_normalize_sport_name_is_stable():
    assert normalize_sport_name("  Functional--Fitness!! ") == "functional fitness"

