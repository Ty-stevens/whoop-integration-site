import json

from app.services.ai.types import AiContext


def weekly_summary_prompt(context: AiContext) -> str:
    return (
        "You are writing advisory training feedback from derived metrics only. "
        "Do not give medical advice. Mention uncertainty when data is sparse. "
        "Return concise plain text with 2-4 observations.\n\n"
        f"Context JSON:\n{json.dumps(context, sort_keys=True)}"
    )


def goal_suggestions_prompt(context: AiContext) -> str:
    return (
        "Suggest weekly training goal changes from derived metrics only. "
        "Do not mutate goals. Return concise plain text with proposed targets and rationale. "
        "The app will parse only fallback-safe suggestions if your output is unstructured.\n\n"
        f"Context JSON:\n{json.dumps(context, sort_keys=True)}"
    )
