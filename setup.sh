#!/usr/bin/env bash
# Check-and-guide onboarding for EVBot. Safe to re-run after fixing any
# single reported issue — it never installs anything without showing you
# the exact command first (except copying .env.example -> .env, which has
# no secrets in it).
set -euo pipefail

cd "$(dirname "$0")"

fail() {
  echo ""
  echo "❌ $1"
  echo ""
  exit 1
}

echo "== EVBot setup =="

# 1. uv
if ! command -v uv >/dev/null 2>&1; then
  fail "uv is not installed. Install it, then re-run ./setup.sh:
    curl -LsSf https://astral.sh/uv/install.sh | sh"
fi
echo "✓ uv found ($(uv --version))"

# 2. ollama
if ! command -v ollama >/dev/null 2>&1; then
  fail "Ollama is not installed. Install it from https://ollama.com/download, then re-run ./setup.sh"
fi
echo "✓ ollama found ($(ollama --version))"

# 3. Ollama server reachable
OLLAMA_HOST_URL="${OLLAMA_HOST:-http://localhost:11434}"
if ! curl -fsS "$OLLAMA_HOST_URL/api/tags" >/dev/null 2>&1; then
  fail "Ollama isn't running at $OLLAMA_HOST_URL. Start it in another terminal, then re-run ./setup.sh:
    ollama serve"
fi
echo "✓ ollama server reachable at $OLLAMA_HOST_URL"

# 4. Required models pulled
SIMPLE_MODEL="${OLLAMA_MODEL_SIMPLE:-llama3.2}"
COMPLEX_MODEL="${OLLAMA_MODEL_COMPLEX:-llama3.1}"
MISSING_MODELS=()
for model in "$SIMPLE_MODEL" "$COMPLEX_MODEL"; do
  # `ollama list` shows tags (e.g. "llama3.2:latest"); strip ":latest" so a
  # bare model name in .env (the common case) still matches.
  if ! ollama list | awk '{print $1}' | sed 's/:latest$//' | grep -qx "$model"; then
    MISSING_MODELS+=("$model")
  fi
done
if [ "${#MISSING_MODELS[@]}" -ne 0 ]; then
  msg="Missing Ollama model(s): ${MISSING_MODELS[*]}. Pull them, then re-run ./setup.sh:"
  for m in "${MISSING_MODELS[@]}"; do
    msg="$msg
    ollama pull $m"
  done
  fail "$msg"
fi
echo "✓ required Ollama models present ($SIMPLE_MODEL, $COMPLEX_MODEL)"

# 5. .env
if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ created .env from .env.example (no API keys required for this pass)"
else
  echo "✓ .env already exists"
fi

# 6. Install deps, ingest KB
echo ""
echo "== Installing dependencies with uv =="
uv sync

echo ""
echo "== Seeding the EV knowledge base =="
uv run python -m evbot.rag.ingest

echo ""
echo "✅ Setup complete. Run the test suite with:"
echo "    uv run pytest"
echo ""
echo "Then launch EVBot with:"
echo "    uv run python -m evbot.app"
