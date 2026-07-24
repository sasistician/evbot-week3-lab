# Week 3 Lab Guide — Skills: Packaging a Recurring Procedure Inside a Real Agent

**Time budget:** ~35-40 min within the 90-min live session, plus ~10 min
pre-class setup (Ollama install + model pulls) — do the setup section before
class if you can.

**Prerequisite:** Today's deck covered Skills — description-driven discovery,
progressive disclosure, and packaging a recurring workflow into something
Claude can invoke on its own without you re-explaining it each time. This lab
is a working chatbot (EVBot) built around that idea: several of its pieces
are procedures you could just as easily package as Skills, and by the end
you'll actually do that with one of them.

---

## 1. Setup

1. Clone the lab repo and run the onboarding script.

   macOS/Linux:
   ```
   git clone https://github.com/sasistician/evbot-week3-lab.git week3-lab
   cd week3-lab
   ./setup.sh
   ```
   Windows: run this from [Git Bash](https://git-scm.com/download/win) (you
   already have it if you can `git clone`) or WSL — native PowerShell/cmd.exe
   can't run `setup.sh` directly:
   ```
   git clone https://github.com/sasistician/evbot-week3-lab.git week3-lab
   cd week3-lab
   bash setup.sh
   ```
2. Follow whatever `setup.sh` prints. It checks for `uv`, Ollama, and the two
   required local models one at a time, and tells you exactly what to install
   or run if something's missing — just fix the one thing it names and
   re-run it (`./setup.sh`, or `bash setup.sh` on Windows) until it reports
   success. No API keys are needed; this lab runs entirely offline once the
   models are pulled.
3. Confirm the baseline passes:
   ```
   uv run pytest
   ```
   All tests should pass.
4. Launch the app:
   ```
   uv run python -m evbot.app
   ```
   Open the printed `localhost:7860` URL. You should see a chat pane on the
   left and an "under the hood" panel on the right — that panel is not
   cosmetic, it's how you'll see every component fire in the steps below.

---

## 2. Quick-reference card

| Piece | File | Role |
|---|---|---|
| Input guardrail | `evbot/guardrails.py` — `check_input_topic` | Rejects/redirects non-EV questions before anything else runs |
| Router | `evbot/router.py` | Decides simple vs. complex — and whether the judge runs at all |
| Knowledge base (RAG) | `evbot/rag/` | Retrieves EV documents relevant to the query |
| Judge | `evbot/judge.py` | For complex queries: scores the small- and large-model answers, picks/merges a winner |
| Output guardrail | `evbot/guardrails.py` — `check_output_safety` | Catches PII, toxicity, and ungrounded claims before the answer is shown |
| Session memory | `evbot/memory.py` | Persists conversation turns across restarts (separate from the KB) |
| Small/large local models | `.env` — `OLLAMA_MODEL_SIMPLE` / `_COMPLEX` | The two models the router chooses between |

---

## 3. The exercise

### Step 1 — Trace a simple, in-KB question

Ask: *"What's the range of the Tesla Model 3?"*

Look at the debug panel. Find the router's decision, the retrieved chunks,
and the final answer.

**Checkpoint:** Confirm `judge` is `null`/empty in the debug trace — for a
simple factual question, the router skips the judge entirely and answers with
the small model alone.

### Step 2 — Push an off-topic question through

Ask: *"What's the weather like tomorrow?"*

**Checkpoint:** Confirm the debug panel shows `early_exit: true` and that
router/RAG/judge never ran — the input guardrail caught it before any of
that work happened.

### Step 3 — Ask a genuinely comparative question

Ask: *"Compare the Chevy Bolt and the Hyundai Ioniq 5 for a first-time EV
buyer."*

**Checkpoint:** Confirm the router sent this down the complex path (both
`small_model_answer` and `large_model_answer` appear in the trace), and read
the judge's `rationale` — does it explain *why* it picked a winner or merged?

### Step 4 — Ask about something the knowledge base doesn't cover

Ask: *"How much does EV insurance typically cost?"*

**Checkpoint:** This isn't covered anywhere in `data/ev_docs/`. Confirm the
output guardrail's groundedness check catches this and you get the honest
"not in my knowledge base" fallback — not a confident-sounding guess.

### Step 5 — Test session memory across a restart

Using the same Session ID box (default `demo`), have a two-turn exchange
where the second turn uses a pronoun:

1. *"Tell me about the Rivian R1T."*
2. *"How much does it cost?"*

**Checkpoint:** Confirm the second answer correctly resolves "it" to the R1T
using conversation history. Then stop the app (Ctrl-C) and restart it
(`uv run python -m evbot.app`), keeping the same Session ID. Ask *"What did I
just ask about?"* — confirm it still remembers, because session memory is
SQLite-backed, not in-process. Contrast this with the knowledge base, which
didn't change at all across that restart.

### Step 6 — Package the judge as a Skill

Open `.claude/skills/answer-quality-judge/SKILL.md` next to `evbot/judge.py`.

**Checkpoint:** Confirm the rubric and decision policy in the Skill match
`judge.py`'s `RUBRIC_PROMPT` — same criteria, same scale, same decision
options. Then, in a Claude Code session in this repo, paste two draft answers
to any question and ask Claude to judge them. Confirm it applies the same
rubric without you re-explaining it.

### Stretch exercises — modify the code, not just trace it

Steps 1-6 traced existing behavior. These ask you to actually change
something and observe the effect.

### Step 7 — Push a guardrail threshold further

Pick one knob in `evbot/config.py` — `GROUNDEDNESS_MAX_UNSUPPORTED` or the
`EV_TOPIC_KEYWORDS` tuple — and loosen it further than its current setting
(both were already loosened once, in an earlier pass, after the small local
model's hedging caused false-positive rejections). For example, raise
`GROUNDEDNESS_MAX_UNSUPPORTED` from `1` to `2`, restart the app, and re-ask
the Step 4 insurance-cost question.

**Checkpoint:** Confirm the previously-blocked question now gets a
confident-sounding answer instead of the "not in my knowledge base"
fallback — then decide for yourself whether that answer is actually
trustworthy. This is the tradeoff every threshold in this file encodes:
fewer false rejections vs. more ungrounded answers slipping through.

### Step 8 — Expand the knowledge base with a new EV model

Add a new file under `data/ev_docs/model_specs/` for an EV not already
covered (e.g. Kia EV6 or Nissan Leaf), following the format of the existing
files in that folder. Re-run ingestion:
```
uv run python -m evbot.rag.ingest
```

**Checkpoint:** Ask a question specific to your new model (e.g. "What's the
range of the Kia EV6?"). Confirm the retrieved chunks in the debug panel
include your new document and the answer is grounded in it, not a
hallucinated guess.

### Step 9 — Swap in a different local model

Pull an Ollama model you haven't used yet (e.g. `ollama pull mistral`, or
another size in the `llama3` family) and point `OLLAMA_MODEL_SIMPLE` or
`OLLAMA_MODEL_COMPLEX` at it in `.env`. Restart the app.

**Checkpoint:** Ask a question that exercises that path (a simple question
for `_SIMPLE`, a comparative one for `_COMPLEX`) and confirm the debug
panel's `small_model_answer`/`large_model_answer` reflects the new model
actually running. Note any difference in answer quality or tone versus the
original model.

### Step 10 — Improve the UI

Open `evbot/app.py` and make one concrete, visible change — for example:
add clickable example-question buttons, surface the router's decision as a
visible badge above the chat instead of leaving it buried in the debug
JSON, or label each assistant turn with which model answered.

**Checkpoint:** Reload the app and confirm your change renders correctly
and doesn't break the existing chat/debug-panel flow.

### Step 11 — Try to improve response latency

The debug trace has no timing information today — add it. Wrap each stage
in `evbot/agent.py`'s `answer_question` (guardrail, retrieval, generation,
judge) with `time.perf_counter()` and add the durations to the `debug`
dict.

**Checkpoint:** Run a comparative query (it exercises every stage) and
identify the slowest stage from your new timings. Then make exactly one
change to speed it up — e.g. lowering `RAG_RETRIEVAL_K_COMPLEX`, or
switching `OLLAMA_MODEL_COMPLEX` to a smaller model — and confirm your
timing instrumentation shows a measurable improvement without breaking
Step 3's checkpoint.

---

## 4. Reflection prompts

1. Which of these pieces would you trust to run fully unattended in
   production, and which would you want a human reviewing before it ships?
2. Why keep session memory and the knowledge base as two separate systems
   instead of one? What would go wrong if you conflated them?
3. The router skips the judge for simple queries — what's the actual cost
   being saved, and is word-count/keyword matching a good enough proxy for
   "this query is simple"? When would it get it wrong?
4. What did packaging the judge as a Skill actually change, given that
   `judge.py` already implements the same logic?

---

## 5. APPLY — your reps this week

- Add a document to `data/ev_docs/` covering the gap from Step 4 (EV
  insurance costs, or another topic you notice is missing), re-run
  `uv run python -m evbot.rag.ingest`, and confirm the fallback disappears.
- Package one of your own recurring evaluation or classification procedures
  as a second Skill, using `answer-quality-judge` as the template.

Bring your biggest find to next session.

---

## Look ahead

Week 4 is **MCP** — connecting Claude to real tools and data sources. The web
search and Claude API integration deferred in this lab are natural
candidates for a W4 MCP server.
