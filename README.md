# EVBot — Week 3 lab

A working EV Q&A agent: input/output guardrails, a router, an LLM-as-judge step,
conversational memory, a RAG knowledge base, a Gradio front end, and `uv`
managing the environment underneath all of it. Runs entirely on local models
via Ollama — no API keys required.

See [`week3-lab-guide.md`](../week3-lab-guide.md) for the actual lab exercise.
This README just gets you running.

## Run it

```
git clone <repo-url>
cd week3-lab
./setup.sh
```

`setup.sh` checks for `uv`, Ollama, and the two required local models, and
tells you exactly what to install if anything's missing — nothing is
installed silently. Once it reports success:

```
uv run pytest              # confirm the baseline is green
uv run python -m evbot.app # launch the Gradio UI at localhost:7860
```
