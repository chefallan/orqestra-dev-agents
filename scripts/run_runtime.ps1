$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

if (-not (Test-Path ".venv")) {
    python -m venv .venv
}

. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python scripts/memory_cli.py init

if (-not $env:AGENT_RUNTIME_API_KEYS) {
    $env:AGENT_RUNTIME_API_KEYS = "local-dev:local-dev-key"
}

if (-not $env:AUTONOMOUS_MAINTENANCE_ENABLED) {
    $env:AUTONOMOUS_MAINTENANCE_ENABLED = "true"
}

if (-not $env:AUTONOMOUS_MAINTENANCE_INTERVAL_SEC) {
    $env:AUTONOMOUS_MAINTENANCE_INTERVAL_SEC = "1800"
}

if (-not $env:PROMPT_QUALITY_MIN_IMPROVEMENT) {
    $env:PROMPT_QUALITY_MIN_IMPROVEMENT = "2.0"
}

if (-not $env:PROMPT_QUALITY_MIN_SCORE) {
    $env:PROMPT_QUALITY_MIN_SCORE = "45"
}

if (-not $env:PROMPT_UPDATE_COOLDOWN_SEC) {
    $env:PROMPT_UPDATE_COOLDOWN_SEC = "1800"
}

# Optional LLM provider configuration (OpenAI-compatible API):
# $env:AGENT_LLM_BASE_URL = "https://api.openai.com/v1"
# $env:AGENT_LLM_API_KEY = "<your-key>"
# $env:AGENT_LLM_MODEL = "gpt-4o-mini"

Write-Host "Runtime auth tenant: local-dev"
Write-Host "Runtime auth key: local-dev-key"
Write-Host "Autonomous maintenance enabled: $env:AUTONOMOUS_MAINTENANCE_ENABLED"
Write-Host "Autonomous maintenance interval (sec): $env:AUTONOMOUS_MAINTENANCE_INTERVAL_SEC"
Write-Host "Prompt quality min improvement: $env:PROMPT_QUALITY_MIN_IMPROVEMENT"
Write-Host "Prompt quality min score: $env:PROMPT_QUALITY_MIN_SCORE"
Write-Host "Prompt update cooldown (sec): $env:PROMPT_UPDATE_COOLDOWN_SEC"
uvicorn runtime.main:app --host 127.0.0.1 --port 64789 --reload
