#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/memory_cli.py init

export AGENT_RUNTIME_API_KEYS="${AGENT_RUNTIME_API_KEYS:-local-dev:local-dev-key}"
export AUTONOMOUS_MAINTENANCE_ENABLED="${AUTONOMOUS_MAINTENANCE_ENABLED:-true}"
export AUTONOMOUS_MAINTENANCE_INTERVAL_SEC="${AUTONOMOUS_MAINTENANCE_INTERVAL_SEC:-1800}"
export PROMPT_QUALITY_MIN_IMPROVEMENT="${PROMPT_QUALITY_MIN_IMPROVEMENT:-2.0}"
export PROMPT_QUALITY_MIN_SCORE="${PROMPT_QUALITY_MIN_SCORE:-45}"
export PROMPT_UPDATE_COOLDOWN_SEC="${PROMPT_UPDATE_COOLDOWN_SEC:-1800}"

# Optional LLM provider configuration (OpenAI-compatible API):
# export AGENT_LLM_BASE_URL="https://api.openai.com/v1"
# export AGENT_LLM_API_KEY="<your-key>"
# export AGENT_LLM_MODEL="gpt-4o-mini"

echo "Runtime auth tenant: local-dev"
echo "Runtime auth key: local-dev-key"
echo "Autonomous maintenance enabled: ${AUTONOMOUS_MAINTENANCE_ENABLED}"
echo "Autonomous maintenance interval (sec): ${AUTONOMOUS_MAINTENANCE_INTERVAL_SEC}"
echo "Prompt quality min improvement: ${PROMPT_QUALITY_MIN_IMPROVEMENT}"
echo "Prompt quality min score: ${PROMPT_QUALITY_MIN_SCORE}"
echo "Prompt update cooldown (sec): ${PROMPT_UPDATE_COOLDOWN_SEC}"
uvicorn runtime.main:app --host 127.0.0.1 --port 64789 --reload
