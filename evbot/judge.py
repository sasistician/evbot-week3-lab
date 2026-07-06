"""LLM-as-judge: compares the small-model and large-model candidate answers.

Only invoked for "complex" queries (see router.py) — the router's decision
to skip this entirely for simple queries is itself a cost-based teaching
point. The rubric here is mirrored exactly in
`.claude/skills/answer-quality-judge/SKILL.md` so the same judgment can be
invoked standalone in Claude Code, outside this running app.
"""

import re
from dataclasses import dataclass
from typing import Literal

from evbot.config import OLLAMA_MODEL_COMPLEX
from evbot.llm_clients import call_llm

RUBRIC_PROMPT = """You are judging two candidate answers to the same question, each \
grounded in the same retrieved context. Score each candidate 1-5 on four criteria:

- Accuracy: does it correctly reflect the context?
- Completeness: does it fully answer the question?
- Groundedness: does it avoid claims unsupported by the context?
- Clarity: is it easy to understand?

Then decide: should the SMALL answer win, the LARGE answer win, or should the two be \
MERGED into a better combined answer? Prefer MERGE only when each answer contributes \
something the other lacks.

QUESTION:
{question}

CANDIDATE A (small model):
{small_answer}

CANDIDATE B (large model):
{large_answer}

Respond in exactly this format:
SMALL_ACCURACY: <1-5>
SMALL_COMPLETENESS: <1-5>
SMALL_GROUNDEDNESS: <1-5>
SMALL_CLARITY: <1-5>
LARGE_ACCURACY: <1-5>
LARGE_COMPLETENESS: <1-5>
LARGE_GROUNDEDNESS: <1-5>
LARGE_CLARITY: <1-5>
WINNER: <small|large|merge>
RATIONALE: <one or two sentences>
MERGED_ANSWER: <only if WINNER is merge, otherwise leave blank>
"""

Winner = Literal["small", "large", "merge"]


@dataclass
class JudgeScores:
    accuracy: int
    completeness: int
    groundedness: int
    clarity: int


@dataclass
class JudgeResult:
    winner: Winner
    answer: str
    rationale: str
    small_scores: JudgeScores
    large_scores: JudgeScores


_FIELD_ORDER = (
    "SMALL_ACCURACY",
    "SMALL_COMPLETENESS",
    "SMALL_GROUNDEDNESS",
    "SMALL_CLARITY",
    "LARGE_ACCURACY",
    "LARGE_COMPLETENESS",
    "LARGE_GROUNDEDNESS",
    "LARGE_CLARITY",
    "WINNER",
    "RATIONALE",
    "MERGED_ANSWER",
)


def _extract_field(raw: str, field: str, default: str = "") -> str:
    # Captures everything up to the next known field marker (or end of text)
    # rather than just the rest of the line — RATIONALE and MERGED_ANSWER can
    # legitimately span multiple lines/paragraphs.
    other_fields = "|".join(f for f in _FIELD_ORDER if f != field)
    pattern = rf"^{field}:\s*(.*?)(?=^(?:{other_fields}):|\Z)"
    match = re.search(pattern, raw, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else default


def _extract_score(raw: str, field: str) -> int:
    value = _extract_field(raw, field, default="3")
    digits = re.search(r"\d", value)
    return int(digits.group()) if digits else 3


def _parse_judge_response(raw: str, small_answer: str, large_answer: str) -> JudgeResult:
    small_scores = JudgeScores(
        accuracy=_extract_score(raw, "SMALL_ACCURACY"),
        completeness=_extract_score(raw, "SMALL_COMPLETENESS"),
        groundedness=_extract_score(raw, "SMALL_GROUNDEDNESS"),
        clarity=_extract_score(raw, "SMALL_CLARITY"),
    )
    large_scores = JudgeScores(
        accuracy=_extract_score(raw, "LARGE_ACCURACY"),
        completeness=_extract_score(raw, "LARGE_COMPLETENESS"),
        groundedness=_extract_score(raw, "LARGE_GROUNDEDNESS"),
        clarity=_extract_score(raw, "LARGE_CLARITY"),
    )
    rationale = _extract_field(raw, "RATIONALE", default="No rationale provided.")

    winner_raw = _extract_field(raw, "WINNER", default="large").lower()
    winner: Winner = "merge" if "merge" in winner_raw else ("small" if "small" in winner_raw else "large")

    if winner == "merge":
        merged = _extract_field(raw, "MERGED_ANSWER")
        answer = merged if merged else f"{small_answer}\n\n{large_answer}"
    elif winner == "small":
        answer = small_answer
    else:
        answer = large_answer

    return JudgeResult(
        winner=winner,
        answer=answer,
        rationale=rationale,
        small_scores=small_scores,
        large_scores=large_scores,
    )


def evaluate(question: str, small_answer: str, large_answer: str) -> JudgeResult:
    raw = call_llm(
        OLLAMA_MODEL_COMPLEX,
        prompt=RUBRIC_PROMPT.format(question=question, small_answer=small_answer, large_answer=large_answer),
    )
    return _parse_judge_response(raw, small_answer, large_answer)
