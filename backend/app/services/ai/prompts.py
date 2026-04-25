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


def benchmark_update_prompt(context: AiContext) -> str:
    return (
        "You update weekly training benchmark targets from derived WHOOP metrics and reports. "
        "Use only the provided derived context; do not infer from raw health data, do not give "
        "medical advice, and keep recommendations conservative when history is sparse. "
        "Return only valid JSON matching this shape: "
        '{"targets":{"zone1_target_minutes":0,"zone2_target_minutes":150,'
        '"zone3_target_minutes":0,"zone4_target_minutes":0,"zone5_target_minutes":0,'
        '"cardio_sessions_target":3,"strength_sessions_target":2},'
        '"summary":"why these targets should change or stay stable",'
        '"confidence":"low|medium|high",'
        '"changes":[{"metric":"zone2_target_minutes","current_value":150,'
        '"recommended_value":150,"reason":"short rationale",'
        '"sources":[{"source_type":"six_month_report","date":"YYYY-MM",'
        '"metric":"zone2_minutes","value":150}]}]}.\n\n'
        f"Context JSON:\n{json.dumps(context, sort_keys=True)}"
    )
