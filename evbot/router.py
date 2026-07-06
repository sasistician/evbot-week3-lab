"""Rule-based router — no LLM call.

Decides whether a query is "simple" (answered by the small model alone,
judge skipped) or "complex" (small + large model both answer, judge picks
between them). This is deliberately the cheap, deterministic counterpart to
the judge's LLM-based comparison a few steps later in the pipeline.
"""

from typing import Literal

from evbot.config import COMPARISON_KEYWORDS, COMPLEXITY_WORD_COUNT_THRESHOLD

KNOWN_MODEL_TOKENS = (
    "model 3",
    "model3",
    "r1t",
    "mach-e",
    "mache",
    "bolt",
    "ioniq",
)

Complexity = Literal["simple", "complex"]


def classify_complexity(query: str) -> Complexity:
    lowered = query.lower()

    word_count = len(query.split())
    if word_count > COMPLEXITY_WORD_COUNT_THRESHOLD:
        return "complex"

    if any(keyword in lowered for keyword in COMPARISON_KEYWORDS):
        return "complex"

    mentioned_models = {token for token in KNOWN_MODEL_TOKENS if token in lowered}
    if len(mentioned_models) > 1:
        return "complex"

    return "simple"
