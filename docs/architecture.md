# EVBot Architecture

## Pipeline (one query, end to end)

```
query
  │
  ▼
memory.get_recent_turns(session_id)          conversational context, distinct from the KB below
  │
  ▼
guardrails.check_input_topic(query)  ──fail──▶  early exit: redirect message, nothing else runs
  │ pass
  ▼
router.classify_complexity(query) ──▶ "simple" | "complex"
  │
  ▼
rag.retriever.retrieve(query)                shared retrieved context for whatever runs next
  │
  ├─ simple:  generate 1 answer (small model)  ──▶ skip judge
  │
  └─ complex: generate 2 answers (small model + large model, same context)
                  │
                  ▼
             judge.evaluate(question, small_answer, large_answer) ──▶ winner / merge
  │
  ▼
guardrails.check_output_safety(answer, context_chunks)
  │  ungrounded claim  ──▶ honest "not in my knowledge base" fallback
  │  PII detected       ──▶ redacted answer
  │  toxicity detected  ──▶ rephrase-request fallback
  │  otherwise          ──▶ answer passes through unchanged
  ▼
memory.append_turn(session_id, "user", query)
memory.append_turn(session_id, "assistant", final_answer)
  │
  ▼
app.py renders the answer + the full debug trace in the "under the hood" panel
```

## Two kinds of "memory" — don't conflate them

This is the single most important distinction in the codebase:

- **Session memory** (`memory.py`, SQLite) — what was *said* in a conversation.
  Turn-by-turn history for one `session_id`, persisted across process
  restarts. It has no idea what a kWh is.
- **Knowledge base** (`rag/`, Chroma) — what's *known* about EVs. A fixed
  (until a student edits `data/ev_docs/`) set of documents retrieved by
  semantic similarity to the current query. It has no idea what you asked
  five minutes ago.

Both are "memory" in a loose sense, but they answer completely different
questions and are wired into the pipeline at different points — memory is
read once at the start of a turn and written once at the end; the KB is
read fresh on every turn based on the query alone.

## Why the router skips the judge for simple queries

Running two model generations plus an LLM-as-judge call is meaningfully more
expensive (in latency and compute) than one small-model generation. The
router's job isn't just "which model answers" — for simple, unambiguous
factual questions, it skips the dual-candidate-plus-judge path entirely. This
mirrors the input guardrail's early exit: both are cost-based short-circuits,
just at different points in the pipeline.

## Deferred extension points

Two things are deliberately not built in this pass, to keep setup local-only
and API-key-free for the lab:

- **Claude API**: `evbot/llm_clients.py` exposes a single `call_llm(model,
  prompt)` function. Adding Claude later means adding a branch inside that
  function (e.g. routing model names that start with `"claude-"` to the
  Anthropic SDK) — no caller elsewhere in the codebase needs to change.
- **Web search**: there is no tool for retrieval outside `data/ev_docs/`.
  The knowledge base is intentionally incomplete in places (see the lab
  guide's Step 4 and APPLY section) — students extend it by adding documents,
  not by reaching for the web. A future pass could add a `tools/web_search.py`
  module alongside the RAG path, following the same "generate two candidates,
  let the judge pick" shape already used for small-vs-large-model answers.
