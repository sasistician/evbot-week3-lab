# EVBot — Week 3 lab

A working EV Q&A agent: input/output guardrails, a router, an LLM-as-judge step,
conversational memory, a RAG knowledge base, a Gradio front end, and `uv`
managing the environment underneath all of it. Runs entirely on local models
via Ollama — no API keys required.

See [`week3-lab-guide.md`](../week3-lab-guide.md) for the actual lab exercise.
This README just gets you running.

## Run it

**macOS / Linux:**
```
git clone https://github.com/sasistician/evbot-week3-lab.git week3-lab
cd week3-lab
./setup.sh
```

**Windows:** run this from [Git Bash](https://git-scm.com/download/win)
(installed alongside Git for Windows — you already have it if you can `git
clone`) or WSL. Native PowerShell/cmd.exe can't run `setup.sh` directly.
```
git clone https://github.com/sasistician/evbot-week3-lab.git week3-lab
cd week3-lab
bash setup.sh
```

`setup.sh` checks for `uv`, Ollama, and the two required local models, and
tells you exactly what to install if anything's missing — nothing is
installed silently. Once it reports success:

```
uv run pytest              # confirm the baseline is green
uv run python -m evbot.app # launch the Gradio UI at localhost:7860
```
