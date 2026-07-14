from evbot import guardrails


def test_input_topic_pass_deterministic():
    result = guardrails.check_input_topic("What's the range of the Tesla Model 3?")
    assert result.passed
    assert result.used_llm_fallback is False


def test_input_topic_ambiguous_falls_back_to_llm(monkeypatch):
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: "no")
    result = guardrails.check_input_topic("What's the weather like tomorrow?")
    assert result.passed is False
    assert result.used_llm_fallback is True


def test_input_topic_ambiguous_llm_says_yes(monkeypatch):
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: "yes")
    result = guardrails.check_input_topic("Tell me about home charger installation costs")
    assert result.passed is True


def test_output_pii_detected_and_redacted(monkeypatch):
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: "NONE")
    answer = "Contact us at sales@example.com for more info."
    result = guardrails.check_output_safety(answer, context_chunks=["some context"])
    assert result.pii_detected
    assert "[REDACTED EMAIL]" in result.redacted_answer


def test_output_toxicity_detected(monkeypatch):
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: "NONE")
    result = guardrails.check_output_safety("You're an idiot for asking that.", context_chunks=["ctx"])
    assert result.toxicity_detected


def test_output_groundedness_pass(monkeypatch):
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: "NONE")
    result = guardrails.check_output_safety("The Model 3 has a 272 mile range.", context_chunks=["Model 3 range: 272 miles"])
    assert result.passed
    assert result.ungrounded_claims == []


def test_output_groundedness_single_unsupported_claim_tolerated(monkeypatch):
    """One flagged sentence is within GROUNDEDNESS_MAX_UNSUPPORTED and should pass."""
    canned_response = "SENTENCE: The Model 3 costs $10.\nVERDICT: UNSUPPORTED\n"
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: canned_response)
    result = guardrails.check_output_safety("The Model 3 costs $10.", context_chunks=["Model 3 range: 272 miles"])
    assert result.passed
    assert not result.groundedness_failed
    assert result.ungrounded_claims == ["The Model 3 costs $10."]


def test_output_groundedness_fail_exceeds_tolerance(monkeypatch):
    canned_response = (
        "SENTENCE: The Model 3 costs $10.\nVERDICT: UNSUPPORTED\n"
        "SENTENCE: The Model 3 seats 12 people.\nVERDICT: UNSUPPORTED\n"
    )
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: canned_response)
    result = guardrails.check_output_safety(
        "The Model 3 costs $10. The Model 3 seats 12 people.",
        context_chunks=["Model 3 range: 272 miles"],
    )
    assert not result.passed
    assert result.groundedness_failed
    assert result.ungrounded_claims == ["The Model 3 costs $10.", "The Model 3 seats 12 people."]


def test_output_no_context_is_ungrounded():
    """No context at all always fails, regardless of the unsupported-claim tolerance."""
    result = guardrails.check_output_safety("Some answer.", context_chunks=[])
    assert not result.passed
    assert result.groundedness_failed
    assert result.ungrounded_claims


def test_output_groundedness_mixed_verdicts_only_flags_unsupported(monkeypatch):
    canned_response = (
        "SENTENCE: The Bolt starts around $27,000.\n"
        "VERDICT: SUPPORTED\n"
        "SENTENCE: The Bolt comes standard with heated seats.\n"
        "VERDICT: UNSUPPORTED\n"
    )
    monkeypatch.setattr(guardrails, "call_llm", lambda *a, **k: canned_response)
    result = guardrails.check_output_safety(
        "The Bolt starts around $27,000. The Bolt comes standard with heated seats.",
        context_chunks=["Bolt EUV starts at $27,000"],
    )
    assert result.passed
    assert result.ungrounded_claims == ["The Bolt comes standard with heated seats."]
