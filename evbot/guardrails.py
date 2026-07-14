"""Input and output guardrails.

Input: a fast deterministic EV-vocabulary allow pass, falling through to a
one-shot LLM classification only when the deterministic pass is ambiguous.
A reject here short-circuits the whole pipeline before router/RAG/judge run.

Output: PII regex scan + keyword-based toxicity check (both deterministic)
bundled with an LLM groundedness check that lists any claim in the answer
not supported by the retrieved context.
"""

import re
from dataclasses import dataclass, field

from evbot.config import (
    EV_TOPIC_KEYWORDS,
    GROUNDEDNESS_MAX_UNSUPPORTED,
    OLLAMA_MODEL_COMPLEX,
    OLLAMA_MODEL_SIMPLE,
)
from evbot.llm_clients import call_llm

_PII_PATTERNS = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "phone": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}

_TOXIC_KEYWORDS = (
    "idiot",
    "stupid",
    "shut up",
    "hate you",
)

_GROUNDEDNESS_PROMPT = """Fact-check each sentence in the ANSWER against the CONTEXT. A \
sentence is SUPPORTED if the CONTEXT contains the underlying fact(s), even when reworded, \
summarized, or compared against another fact also in the CONTEXT. Ignore subjective \
commentary/opinions — treat those as SUPPORTED too. A sentence is UNSUPPORTED only if it \
states a concrete fact (a number, spec, price, name) found nowhere in the CONTEXT.

For each sentence in the ANSWER, output exactly two lines:
SENTENCE: <the sentence>
VERDICT: SUPPORTED or UNSUPPORTED

CONTEXT:
{context}

ANSWER:
{answer}
"""


@dataclass
class InputGuardrailResult:
    passed: bool
    reason: str | None = None
    used_llm_fallback: bool = False


@dataclass
class OutputGuardrailResult:
    passed: bool
    pii_detected: bool = False
    toxicity_detected: bool = False
    ungrounded_claims: list[str] = field(default_factory=list)
    groundedness_failed: bool = False
    redacted_answer: str | None = None


def check_input_topic(query: str, history: str = "") -> InputGuardrailResult:
    lowered = query.lower()

    if any(keyword in lowered for keyword in EV_TOPIC_KEYWORDS):
        return InputGuardrailResult(passed=True)

    # A short follow-up like "how much does it cost?" has no EV keywords of
    # its own — the LLM fallback needs the recent conversation to resolve
    # pronouns like "it" before judging whether the question is on-topic.
    classification = call_llm(
        OLLAMA_MODEL_SIMPLE,
        prompt=f"RECENT CONVERSATION:\n{history or '(none)'}\n\nQuestion: {query}",
        system=(
            "Is the following question about electric vehicles (EVs) — including EV "
            "models, charging, batteries, incentives, or maintenance? It may be a "
            "short follow-up (e.g. using \"it\" or \"that\") that only makes sense "
            "given the recent conversation provided — use that context to resolve "
            "what it's referring to before judging. Respond with only one word: "
            "yes or no."
        ),
    )
    # Default-permissive on an ambiguous/empty model response — only an
    # explicit "no" rejects the question. A strict "must start with yes"
    # check was rejecting on-topic follow-ups whenever the small local model
    # hedged its answer.
    is_ev_related = not classification.strip().lower().startswith("n")

    return InputGuardrailResult(
        passed=is_ev_related,
        reason=None if is_ev_related else "Question does not appear to be about EVs.",
        used_llm_fallback=True,
    )


def _scan_pii(answer: str) -> tuple[bool, str]:
    redacted = answer
    detected = False
    for label, pattern in _PII_PATTERNS.items():
        if pattern.search(redacted):
            detected = True
            redacted = pattern.sub(f"[REDACTED {label.upper()}]", redacted)
    return detected, redacted


def _scan_toxicity(answer: str) -> bool:
    lowered = answer.lower()
    return any(keyword in lowered for keyword in _TOXIC_KEYWORDS)


def _parse_sentence_verdicts(raw: str) -> list[str]:
    """Extract sentences the model explicitly labeled UNSUPPORTED.

    Asking the model to label every sentence (rather than filter down to
    just the unsupported ones) turned out to be far more reliable with small
    local models — filtering-by-omission is a harder instruction to follow
    than "classify each item," even though the two are logically equivalent.
    """
    sentence = None
    unsupported = []
    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("SENTENCE:"):
            sentence = line.split(":", 1)[1].strip()
        elif line.upper().startswith("VERDICT:") and sentence is not None:
            if "UNSUPPORTED" in line.upper():
                unsupported.append(sentence)
            sentence = None
    return unsupported


def _check_groundedness(answer: str, context_chunks: list[str]) -> list[str]:
    if not context_chunks:
        return ["No retrieved context was available to support this answer."]

    context = "\n\n".join(context_chunks)
    response = call_llm(
        OLLAMA_MODEL_COMPLEX,
        prompt=_GROUNDEDNESS_PROMPT.format(context=context, answer=answer),
    )
    return _parse_sentence_verdicts(response)


def check_output_safety(answer: str, context_chunks: list[str]) -> OutputGuardrailResult:
    pii_detected, redacted = _scan_pii(answer)
    toxicity_detected = _scan_toxicity(answer)
    ungrounded_claims = _check_groundedness(answer, context_chunks)

    # Tolerate a small number of flagged sentences rather than rejecting the
    # whole answer over one mis-scored claim. Having no context at all to
    # check against is a harder failure than a few flagged sentences, so
    # that case always fails regardless of the tolerance.
    groundedness_failed = (
        not context_chunks or len(ungrounded_claims) > GROUNDEDNESS_MAX_UNSUPPORTED
    )

    passed = not pii_detected and not toxicity_detected and not groundedness_failed

    return OutputGuardrailResult(
        passed=passed,
        pii_detected=pii_detected,
        toxicity_detected=toxicity_detected,
        ungrounded_claims=ungrounded_claims,
        groundedness_failed=groundedness_failed,
        redacted_answer=redacted if pii_detected else None,
    )
