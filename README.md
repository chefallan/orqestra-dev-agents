# Autonomous Multi-Assistant Agent System (Orchestrator + Specialists)

This repository sets up a multi-agent workflow where you talk to one Orchestrator agent, and it coordinates specialist agents to plan, build, test, and retain project context.

Primary environment: VS Code with GitHub Copilot Chat in Agent mode. Portable workspace files are also included for Claude, Codex, OpenCode, and similar assistants.

## What You Get

- Single entrypoint orchestrator: `agents/orchestrator.agents.md`
- Specialist agents for product, architecture, implementation, security, QA, documentation, and memory
- Standardized handoff contract: `agents/contracts/handoff-contract.md`
- Autonomous delivery loop: `agents/workflows/autonomous-webapp-loop.md`
- Persistent searchable memory: SQLite + FTS via `scripts/memory_cli.py`
- Runnable autonomous runtime API: `runtime/agent_runtime/`
- Orchestrator-led prompt enhancement endpoint that stores enhanced prompts in `agents/`
- Documentation Agent that updates architecture and change logs during each run

## Folder Layout

- `agents/`: portable agent specs
- `agents/contracts/`: Delegation contracts
- `agents/workflows/`: Operating workflow
- `agents/memory/`: Long-term context artifacts and DB schema
- `templates/`: Reusable ticket template for delegation
- `scripts/`: Utility scripts for memory operations

## Scope and Compatibility

- First-class support: VS Code with GitHub Copilot Chat in Agent mode.
- Portable support: Claude, Codex, OpenCode, and similar assistants through `AGENTS.md`, `.github/skills/orqestra-workflow/SKILL.md`, and the markdown agent specs under `agents/`.
- Other IDE/editor integrations may still require manual setup, and feature parity with Copilot chat modes is not guaranteed.

## Quick Start

1. Open this repository in VS Code.
2. Open your coding assistant.
3. For Copilot, open Agent mode and select the orchestrator chat mode or agent spec.
4. For Claude, Codex, OpenCode, and similar assistants, start from `AGENTS.md` or `.github/skills/orqestra-workflow/SKILL.md`.
5. Give a goal, for example:
   - "Build an MVP SaaS web app for appointment booking with Stripe checkout and admin analytics."
5. Let the orchestrator create and delegate handoff tickets using the contract.

## First 5 Minutes (New Repo)

If you are using the npm package in your own repository, follow this exact flow:

1. Install the tool

```bash
npm install -D orqestra-dev-agents@latest
```

2. Initialize files (full production setup)

```bash
npx orqestra-dev-agents init --with-runtime --with-contracts
```

If `package.json` is not present, `init` creates a minimal one automatically so start/stop scripts are available.

3. Validate files are present

```bash
npx orqestra-dev-agents doctor --with-runtime --with-contracts
```

4. Install VS Code dependencies:

```bash
npx orqestra-dev-agents install-vscode
```

5. Start autonomous runtime (recommended):

```bash
npm run orqestra:start
```

If your repo does not yet have a `package.json`, use the direct command:

```bash
npx orqestra-dev-agents runtime start
```

6. Open the repo in VS Code or your coding assistant.

7. Pick the best entrypoint for that assistant.
   - Copilot: `.github/copilot-instructions.md` or `agents/orchestrator.agents.md`
   - Claude, Codex, OpenCode, and similar assistants: `AGENTS.md` or `.github/skills/orqestra-workflow/SKILL.md`

8. Send one single automation objective prompt:

```text
Build and automate a production-ready MVP with signup/login, project creation, tests, docs updates, and memory snapshots. Execute in thin vertical slices until a releasable first version is ready, and report progress after each slice.
```

That is enough to start. The orchestrator should handle planning and specialist delegation from there.

## npm Package Bootstrap

This repo also contains an installable npm package at `packages/orqestra-dev-agents`.

Install it in any target repository that you plan to operate from VS Code:

```bash
npm install -D orqestra-dev-agents
```

Initialize orchestrator + specialist setup:

```bash
npx orqestra-dev-agents init
```

Initialize only core files (no memory/docs scaffolding):

```bash
npx orqestra-dev-agents init --minimal
```

Initialize with runtime, scripts, templates, and requirements:

```bash
npx orqestra-dev-agents init --with-runtime
```

Initialize with agent contracts and handoff templates:

```bash
npx orqestra-dev-agents init --with-contracts
```

Validate required agent files:

```bash
npx orqestra-dev-agents doctor
```

Validate minimal mode requirements only:

```bash
npx orqestra-dev-agents doctor --minimal
```

Validate runtime and contracts presence:

```bash
npx orqestra-dev-agents doctor --with-runtime --with-contracts
```

Control runtime with one command:

```bash
npx orqestra-dev-agents runtime start
npx orqestra-dev-agents runtime status
npx orqestra-dev-agents runtime stop
```

Compact daily-use commands:

```bash
npx orqestra-dev-agents hub
npx orqestra-dev-agents agents orchestrator
npx orqestra-dev-agents workflows autonomous-webapp-loop
npx orqestra-dev-agents contracts handoff-contract
npx orqestra-dev-agents tools handoff --from orchestrator --to webapp-builder --epic compact-cli
```

Optional skills lookup sources:

- `skills/` in the current repository
- `.agents/skills/` in the current repository
- `.github/skills/` in the current repository
- `~/.claude/skills/`
- directories listed in `ORQESTRA_SKILLS_DIRS`

Portable assistant entrypoints generated by the package:

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/skills/orqestra-workflow/SKILL.md`

Supported agent skill installs are built into the CLI. Use `npx orqestra-dev-agents skills agents` to list the full registry and `npx orqestra-dev-agents skills install orqestra-workflow --agent <id> --scope project|global` to install into agent-specific skill directories such as `.claude/skills/`, `.agents/skills/`, `.continue/skills/`, `.cursor/skills`, `.codex/skills`, `.config/opencode/skills/`, and the other supported paths.

## Runnable Runtime (Code-Driven Delegation)

Preferred CLI control (includes Python/runtime prerequisite checks on start):

```bash
npx orqestra-dev-agents runtime start
```

Then use status/stop when needed:

```bash
npx orqestra-dev-agents runtime status
npx orqestra-dev-agents runtime stop
```

Alternative direct scripts:

Start the runtime with one command:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_runtime.ps1
```

Or on Ubuntu/macOS:

```bash
bash scripts/run_runtime.sh
```

Runtime API base URL: `http://127.0.0.1:64789`

Autonomous maintenance is enabled by default:
- The runtime periodically re-enhances prompt files in `agents/` without user interaction.
- This runs for each configured tenant in `AGENT_RUNTIME_API_KEYS`.
- Default interval is every 1800 seconds (30 minutes).
- Prompt updates are quality-gated; a new version is saved only if score and improvement thresholds are met.
- Prompt updates are cooldown-gated; files are not rewritten again until cooldown expires.

Default local credentials (from `scripts/run_runtime.ps1` or `scripts/run_runtime.sh`):
- Tenant: `local-dev`
- API key: `local-dev-key`

All runtime API requests require headers:
- `X-Tenant-Id: local-dev`
- `X-Api-Key: local-dev-key`

The API examples below use PowerShell (`Invoke-RestMethod`). On Ubuntu/macOS, use equivalent `curl` commands with the same headers and JSON payloads.

Create a new orchestrated run:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:64789/runs" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"} -ContentType "application/json" -Body '{"objective":"Build an MVP SaaS web app with multi-tenant auth and billing","context":{"priority":"speed"}}'
```

Send a seed prompt to orchestrator and store enhanced agent spec in `agents/`:

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:64789/prompts/enhance" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"} -ContentType "application/json" -Body '{"title":"Backend API Agent","seed_prompt":"Build robust FastAPI endpoints with tests and migrations.","target_file":"backend-api-agent.agents.md"}'
```

Emergency manual override (bypass cooldown only for this request):

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:64789/prompts/enhance" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"} -ContentType "application/json" -Body '{"title":"Backend API Agent","seed_prompt":"Build robust FastAPI endpoints with tests and migrations.","target_file":"backend-api-agent.agents.md","bypass_cooldown":true}'
```

Then inspect the created task output to get `saved_prompt_path` via:
- `GET /tasks/{task_id}`
- If a prompt was not better, task artifacts include `quality_gate.decision=skipped` with reason.
- If a prompt is within cooldown, task artifacts include remaining cooldown seconds.
- Manual override keeps quality checks active but bypasses cooldown for that call only.

Check autonomous scheduler status:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:64789/autonomy/status" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"}
```

List runs:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:64789/runs" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"}
```

List all tasks for one run:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:64789/runs/<RUN_ID>/tasks" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"}
```

Get compact autonomy health for one run:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:64789/runs/<RUN_ID>/autonomy-health" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"}
```

Search long-term memory:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:64789/memory/search?query=architecture" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"}
```

List dead-letter tasks for a run:

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:64789/runs/<RUN_ID>/dead-letter" -Headers @{"X-Tenant-Id"="local-dev";"X-Api-Key"="local-dev-key"}
```

The runtime automatically executes this sequence per run:
1. Orchestrator
2. Product Manager and Context Indexing (parallel branch)
3. System Architect
4. WebApp Builder
5. Security Auditor
6. QA/Reliability
7. Documentation Agent
8. Memory Steward Snapshot (joins Security + QA + Context + Docs branch)

Runtime reliability controls:
- Dependency graph scheduling (not only linear chaining)
- Per-task retry counter (`retry_count`, `max_retries`)
- Dead-letter queue per run for tasks that exhaust retries
- Tenant-isolated visibility for runs/tasks/memory

Runtime documentation controls:
- Documentation Agent writes ongoing updates to `docs/autogenerated/ARCHITECTURE.md`
- Documentation Agent writes ongoing change logs to `docs/autogenerated/CHANGES.md`

Autonomous prompt controls:
- `AUTONOMOUS_MAINTENANCE_ENABLED=true|false`
- `AUTONOMOUS_MAINTENANCE_INTERVAL_SEC=<seconds>` (minimum 60)
- `PROMPT_QUALITY_MIN_IMPROVEMENT=<float>`
- `PROMPT_QUALITY_MIN_SCORE=<float>`
- `PROMPT_UPDATE_COOLDOWN_SEC=<seconds>`

## One Prompt Automation Build

Use this prompt to kick off end-to-end autonomous building from one message:

```text
Build and automate a production-ready MVP with signup/login, project creation, tests, docs updates, and memory snapshots. Execute in thin vertical slices until a releasable first version is ready, and report progress after each slice.
```

Suggested flow:

1. `npx orqestra-dev-agents runtime start`
2. Open your coding assistant.
3. Use `AGENTS.md`, `.github/copilot-instructions.md`, `.github/skills/orqestra-workflow/SKILL.md`, or `agents/orchestrator.agents.md` depending on what it supports.
4. Send the single objective above in chat.
5. Track progress/runtime health: `npx orqestra-dev-agents runtime status`
6. Stop runtime when done: `npx orqestra-dev-agents runtime stop`

## Memory Setup

Initialize memory database:

```powershell
python scripts/memory_cli.py init
```

Write memory after each milestone:

```powershell
python scripts/memory_cli.py upsert --key sprint-1-summary --type milestone --tags "mvp,backend" --content "Finished auth and tenant-aware project setup" --source "ticket-001"
```

Retrieve context for any agent task:

```powershell
python scripts/memory_cli.py search --query "tenant auth decisions" --limit 8
```

## Recommended Orchestrator Routine

1. Intake request and define outcome + success metric.
2. Delegate product framing.
3. Delegate architecture.
4. Delegate implementation in vertical slices.
5. Delegate QA pass.
6. Persist memory snapshot.
7. Report status and next best slice.

## Handoff Discipline (Important)

Every delegation must include:

- Clear scope boundaries
- Testable acceptance criteria
- Validation commands
- Return payload with evidence

Use `templates/handoff-ticket.template.md` for consistency.

You can auto-generate a ticket with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/new_handoff_ticket.ps1 -From "Orchestrator" -To "WebAppBuilder" -Epic "MVP Foundation" -Priority P1
```

Or on Ubuntu/macOS:

```bash
bash scripts/new_handoff_ticket.sh --from "Orchestrator" --to "WebAppBuilder" --epic "MVP Foundation" --priority P1
```

## Notes

- Keep the orchestrator as the only user-facing agent.
- Keep specialist outputs concise and machine-actionable.
- Treat `agents/memory/context-ledger.md` and SQLite memory as source of truth for continuity.
- Specialists are LLM-backed when `AGENT_LLM_BASE_URL` and `AGENT_LLM_API_KEY` are set, with deterministic fallback for local development.

## Prompt Contract Validation

This repository includes automated contract drift checks between prompt-declared JSON schemas and runtime-enforced schemas.

Run locally:

```powershell
python scripts/validate_prompt_contracts.py --repo-root .
```

CI workflow:

- `.github/workflows/prompt-contracts-ci.yml`
- Runs on push and pull requests
- Compiles runtime Python modules
- Fails if prompt and runtime schemas drift

## Troubleshooting Install vs Init

If the package is installed (for example `orqestra-dev-agents --version` works) but files are not visible, initialization has not been run in the current target project yet.

Run in the project where you want files generated:

```bash
npx orqestra-dev-agents@latest init
npx orqestra-dev-agents@latest doctor
```

To overwrite existing generated files:

```bash
npx orqestra-dev-agents@latest init --force
```

If you are unsure what to do next in a repo, run:

```bash
npx orqestra-dev-agents@latest onboarding
```

