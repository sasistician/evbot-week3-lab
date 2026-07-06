---
name: answer-quality-judge
description: Score two candidate answers to the same question on Accuracy, Completeness, Groundedness, and Clarity, then decide a winner or merge. Use when asked to "score these answers," "judge these candidates," "which response is better," or to evaluate/compare draft answers against a rubric.
---

# Answer Quality Judge

This is the same rubric `evbot/judge.py` uses at runtime to compare EVBot's
small-model and large-model candidate answers — packaged here so it can be
invoked standalone, outside the running app (e.g. on answers pasted into a
Claude Code session, or re-applied to a batch of past conversation logs).

## Rubric

Score each candidate 1-5 on four criteria:

- **Accuracy** — does it correctly reflect the provided context?
- **Completeness** — does it fully answer the question?
- **Groundedness** — does it avoid claims unsupported by the context?
- **Clarity** — is it easy to understand?

## Decision policy

After scoring, decide one of:

- **Winner: small** — the small-model candidate is simply better across most criteria.
- **Winner: large** — same, in the other direction.
- **Merge** — each candidate contributes something the other lacks (e.g. one
  is more complete, the other more grounded). Only choose this when a
  combined answer would genuinely be better than either alone — don't merge
  by default just because scores are close.

## Worked example

**Question:** "How much does the Chevy Bolt cost and what's its range?"

**Small-model answer:** "The Bolt EUV starts around $27,000-$30,000 before
incentives."

**Large-model answer:** "The Bolt EUV starts around $27,000-$30,000 before
incentives, and offers an EPA-estimated range of about 247-259 miles."

Scoring:
```
Small: Accuracy 5, Completeness 2, Groundedness 5, Clarity 5
Large: Accuracy 5, Completeness 5, Groundedness 5, Clarity 5
Winner: large
Rationale: The small answer is accurate but only answers half the question
(price, no range); the large answer answers both parts and is equally
well-grounded.
```

## Expected output shape

When invoked, respond with:

```
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
```

This is the exact format `evbot/judge.py`'s `RUBRIC_PROMPT` asks the local
model for — the lab guide has students diff this file against that prompt to
confirm both encode the same judgment.
