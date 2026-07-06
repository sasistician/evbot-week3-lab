from evbot import judge

CANNED_RESPONSE_LARGE_WINS = """SMALL_ACCURACY: 3
SMALL_COMPLETENESS: 2
SMALL_GROUNDEDNESS: 4
SMALL_CLARITY: 3
LARGE_ACCURACY: 5
LARGE_COMPLETENESS: 5
LARGE_GROUNDEDNESS: 5
LARGE_CLARITY: 4
WINNER: large
RATIONALE: The large answer is more complete and accurate.
MERGED_ANSWER:
"""

CANNED_RESPONSE_MERGE = """SMALL_ACCURACY: 4
SMALL_COMPLETENESS: 3
SMALL_GROUNDEDNESS: 5
SMALL_CLARITY: 4
LARGE_ACCURACY: 4
LARGE_COMPLETENESS: 5
LARGE_GROUNDEDNESS: 3
LARGE_CLARITY: 4
WINNER: merge
RATIONALE: Small is more grounded, large is more complete.
MERGED_ANSWER: The combined, best-of-both answer.
"""


def test_judge_picks_large_winner(monkeypatch):
    monkeypatch.setattr(judge, "call_llm", lambda *a, **k: CANNED_RESPONSE_LARGE_WINS)

    result = judge.evaluate("What's the range?", small_answer="short answer", large_answer="detailed answer")

    assert result.winner == "large"
    assert result.answer == "detailed answer"
    assert result.large_scores.completeness == 5
    assert result.small_scores.completeness == 2


def test_judge_merges_when_requested(monkeypatch):
    monkeypatch.setattr(judge, "call_llm", lambda *a, **k: CANNED_RESPONSE_MERGE)

    result = judge.evaluate("Compare A and B", small_answer="answer A", large_answer="answer B")

    assert result.winner == "merge"
    assert result.answer == "The combined, best-of-both answer."


def test_judge_falls_back_to_concatenation_if_merge_answer_missing(monkeypatch):
    response = CANNED_RESPONSE_MERGE.replace("MERGED_ANSWER: The combined, best-of-both answer.", "MERGED_ANSWER:")
    monkeypatch.setattr(judge, "call_llm", lambda *a, **k: response)

    result = judge.evaluate("Compare A and B", small_answer="answer A", large_answer="answer B")

    assert result.winner == "merge"
    assert "answer A" in result.answer
    assert "answer B" in result.answer


def test_judge_defaults_missing_scores_to_three(monkeypatch):
    monkeypatch.setattr(judge, "call_llm", lambda *a, **k: "WINNER: small\nRATIONALE: ok\n")

    result = judge.evaluate("q", small_answer="a", large_answer="b")

    assert result.winner == "small"
    assert result.small_scores.accuracy == 3
