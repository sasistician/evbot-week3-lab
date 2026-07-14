"""Orchestrator — ties every component together for one turn of conversation.

See docs/architecture.md for the full data-flow diagram. In short:

guardrail-in -> router -> RAG retrieve -> generate (1 or 2 candidates) ->
judge (only for complex queries) -> guardrail-out -> memory write

`answer_question` returns both the user-facing answer and a `debug` dict
describing every step, so the Gradio "under the hood" panel can render the
whole trace.
"""

from dataclasses import asdict
from typing import Any

from evbot import guardrails, memory, router
from evbot.config import (
    MEMORY_RECENT_TURNS,
    OLLAMA_MODEL_COMPLEX,
    OLLAMA_MODEL_SIMPLE,
    RAG_RETRIEVAL_K,
    RAG_RETRIEVAL_K_COMPLEX,
)
from evbot.judge import evaluate as judge_evaluate
from evbot.llm_clients import call_llm
from evbot.rag.retriever import retrieve

_GENERATION_SYSTEM_PROMPT = """You are EVBot, an assistant that answers questions about \
electric vehicles using only the CONTEXT provided below. If the context doesn't contain \
the answer, say so plainly rather than guessing. Keep answers concise.

CONTEXT:
{context}

RECENT CONVERSATION:
{history}
"""

_NOT_GROUNDED_FALLBACK = (
    "I don't have reliable, grounded information to answer that confidently — it may not "
    "be covered in my current knowledge base yet. Feel free to rephrase, ask something else "
    "about EVs, or add a document covering this to data/ev_docs/ (see the lab guide's APPLY "
    "step)."
)

_TOXIC_FALLBACK = "I can't provide that response as phrased. Could you rephrase your question?"


def _format_history(turns: list[memory.Turn]) -> str:
    if not turns:
        return "(no prior turns)"
    return "\n".join(f"{t.role}: {t.content}" for t in turns)


def _generate_answer(model: str, query: str, context_chunks: list[str], history: str) -> str:
    system = _GENERATION_SYSTEM_PROMPT.format(
        context="\n\n".join(context_chunks) if context_chunks else "(no context retrieved)",
        history=history,
    )
    return call_llm(model, prompt=query, system=system)


def answer_question(query: str, session_id: str) -> tuple[str, dict[str, Any]]:
    debug: dict[str, Any] = {"query": query}

    recent_turns = memory.get_recent_turns(session_id, n=MEMORY_RECENT_TURNS)
    history = _format_history(recent_turns)

    input_result = guardrails.check_input_topic(query, history=history)
    debug["input_guardrail"] = asdict(input_result)

    if not input_result.passed:
        debug["early_exit"] = True
        redirect = "I'm EVBot — I can only help with questions about electric vehicles. Try asking about EV models, charging, batteries, or incentives."
        memory.append_turn(session_id, "user", query)
        memory.append_turn(session_id, "assistant", redirect)
        return redirect, debug

    debug["early_exit"] = False

    complexity = router.classify_complexity(query)
    debug["router_decision"] = complexity

    retrieval_k = RAG_RETRIEVAL_K_COMPLEX if complexity == "complex" else RAG_RETRIEVAL_K
    context_chunks = retrieve(query, k=retrieval_k)
    debug["retrieved_chunks"] = context_chunks

    small_answer = _generate_answer(OLLAMA_MODEL_SIMPLE, query, context_chunks, history)
    debug["small_model_answer"] = small_answer

    if complexity == "simple":
        candidate_answer = small_answer
        debug["judge"] = None
    else:
        large_answer = _generate_answer(OLLAMA_MODEL_COMPLEX, query, context_chunks, history)
        debug["large_model_answer"] = large_answer

        judge_result = judge_evaluate(query, small_answer, large_answer)
        candidate_answer = judge_result.answer
        debug["judge"] = {
            "winner": judge_result.winner,
            "rationale": judge_result.rationale,
            "small_scores": asdict(judge_result.small_scores),
            "large_scores": asdict(judge_result.large_scores),
        }

    output_result = guardrails.check_output_safety(candidate_answer, context_chunks)
    debug["output_guardrail"] = asdict(output_result)

    if output_result.groundedness_failed:
        final_answer = _NOT_GROUNDED_FALLBACK
    elif output_result.pii_detected:
        final_answer = output_result.redacted_answer or candidate_answer
    elif output_result.toxicity_detected:
        final_answer = _TOXIC_FALLBACK
    else:
        final_answer = candidate_answer

    debug["final_answer"] = final_answer

    memory.append_turn(session_id, "user", query)
    memory.append_turn(session_id, "assistant", final_answer)

    return final_answer, debug
