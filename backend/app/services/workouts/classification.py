import re
from typing import Literal

WorkoutClassification = Literal["cardio", "strength", "other", "unknown"]

CARDIO_SPORTS = {
    "cycling",
    "elliptical",
    "hiking",
    "indoor cycling",
    "rowing",
    "running",
    "stair climber",
    "swimming",
    "trail running",
    "treadmill",
    "walking",
}

STRENGTH_SPORTS = {
    "calisthenics",
    "functional fitness",
    "pilates",
    "resistance training",
    "strength trainer",
    "weightlifting",
}


def normalize_sport_name(sport_name: str | None) -> str:
    if sport_name is None:
        return ""
    normalized = sport_name.casefold().strip()
    normalized = re.sub(r"[_\-/]+", " ", normalized)
    normalized = re.sub(r"[^a-z0-9 ]+", "", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def classify_workout_sport(sport_name: str | None) -> WorkoutClassification:
    normalized = normalize_sport_name(sport_name)
    if not normalized:
        return "unknown"
    if normalized in CARDIO_SPORTS:
        return "cardio"
    if normalized in STRENGTH_SPORTS:
        return "strength"
    return "unknown"

