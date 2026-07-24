# EVBot — Week 3 lab (working notes)

Teaching lab for the AI-First Engineer course. Pairs with
`../week3-lab-guide.md` and the `week3-skills-broadside.html` /
`week3-lab-deep-dive-broadside.html` decks (all one directory up, in
`softwareEngineersCourse/`) — this repo is the hands-on companion, not
standalone course material. Public mirror: `github.com/sasistician/evbot-week3-lab`
(origin remote already set).

## What it is

An EV Q&A agent demonstrating, end to end: input/output guardrails, a
complexity router, an LLM-as-judge step, conversational memory, a RAG
knowledge base, and a Gradio UI — entirely on local Ollama models, no API
keys required. Full pipeline diagram and design rationale live in
[docs/architecture.md](docs/architecture.md) — read that before touching
`evbot/agent.py`, not this file.

## Tooling & commands

- `uv` + `pyproject.toml` (Python >=3.11). Ollama models: `llama3.2`
  (simple queries), `llama3.1` (complex queries) — overridable via `.env`.
- `./setup.sh` — check-and-guide only (uv, Ollama, models). Never add
  silent auto-install to it.
- `uv run pytest` — test suite (tests/ mirrors evbot/ module-by-module).
- `uv run python -m evbot.app` — Gradio UI at localhost:7860.

## Non-obvious gotchas

- **Guardrails are deliberately lenient, not strict-by-default.** The
  input topic filter is default-permissive (rejects only on an explicit
  "no" from the LLM fallback) and the output groundedness check tolerates
  up to `GROUNDEDNESS_MAX_UNSUPPORTED` (config.py) flagged sentences
  before falling back. Both were loosened after the small local model's
  hedging answers caused false-positive rejections on legitimate
  on-topic queries. Don't tighten these back to strict without re-testing
  against the local models' actual hedging behavior first.
- **"Memory" means two unrelated things in this codebase** — session
  memory (`memory.py`, SQLite, turn history) vs. the RAG knowledge base
  (`rag/`, Chroma, EV facts). See docs/architecture.md for the full
  distinction; don't conflate them in code or in the lab guide.
- Claude API and web search are intentionally *not* wired in
  (`evbot/llm_clients.py` has a single-branch-point extension seam for
  Claude; there's no web-search tool). This is a deliberate scope
  boundary for the lab, not a gap to fill proactively.
