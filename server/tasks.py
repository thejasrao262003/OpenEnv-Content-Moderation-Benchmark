from models import TaskConfig

TASKS: dict[str, TaskConfig] = {
    "easy_harassment": TaskConfig(
        task_id="easy_harassment",
        difficulty="easy",
        description=(
            "A post with an explicit death threat targeted at a named individual. "
            "The user has 2 prior violations on record. US geo. Clear harassment."
        ),
        max_steps=6,
        seed=42,
    ),
    "medium_ambiguous": TaskConfig(
        task_id="medium_ambiguous",
        difficulty="medium",
        description=(
            "A negative product review that uses aggressive language but no direct threat. "
            "EU geo with stricter misinformation policy. Borderline restricted content."
        ),
        max_steps=8,
        seed=100,
    ),
    "hard_misinformation": TaskConfig(
        task_id="hard_misinformation",
        difficulty="hard",
        description=(
            "A post claiming vaccines cause autism, shared with high engagement. "
            "IN geo, low direct reports but viral spread. Conflicting context signals."
        ),
        max_steps=10,
        seed=777,
    ),
}
