# Autonomous WebApp Delivery Loop

This workflow lets one Orchestrator coordinate specialists from idea to release.

## Phase 0: Intake
- Capture problem, users, and success metrics.
- Ask only blocking questions.
- Create a first-pass roadmap.

## Phase 1: Product Framing
- Delegate to Product Manager.
- Output: backlog, acceptance criteria, MVP boundaries.

## Phase 2: Architecture
- Delegate to System Architect.
- Output: ADRs, data model, API contracts, deployment model.

## Phase 3: Build Slice-by-Slice
- Delegate to WebApp Builder in thin vertical slices.
- Enforce test coverage and migration discipline.
- Require AC-by-AC status and validation evidence per slice.

### Slice Quality Gate (mandatory before phase handoff)
- One user outcome per slice.
- Acceptance criteria are explicit and testable.
- Changed interfaces are listed (API, DB, UI, config, jobs/events).
- Validation commands are executed and outcomes recorded.
- Contract drift check is explicitly reported.

## Phase 4: Security Audit
- Delegate to Security Auditor.
- Produce vulnerability findings, severity, and remediation plan.

## Phase 5: Verify
- Delegate to QA/Reliability.
- Require pass/fail recommendation with evidence.

## Phase 6: Document
- Delegate to Documentation Agent.
- Update architecture and change logs from verified outputs.

## Phase 7: Memory Persist
- Delegate to Memory Steward.
- Update context ledger and decision log.

## Phase 8: Orchestrator Report
- Share progress, blockers, and next action.
- Propose the next highest-value slice.

## Prompt Enhancement Flow
- User sends seed prompt to Orchestrator via `POST /prompts/enhance`.
- Orchestrator improves prompt quality and persists result to `agents/`.
- Saved prompt path is returned in task artifacts for traceability.

## Autonomous Maintenance
- Runtime executes periodic prompt enhancement in the background with no user input.
- All prompt files under `agents/*.agents.md` are included automatically.
- Control with environment variables:
	- `AUTONOMOUS_MAINTENANCE_ENABLED`
	- `AUTONOMOUS_MAINTENANCE_INTERVAL_SEC`
- Inspect state with `GET /autonomy/status`.

## Cadence Rules
- Keep cycle time short (1 to 2 days per slice).
- One active P0 ticket at a time.
- Close loop only when memory is updated.

## Runtime Operation
- Start API runtime: `powershell -ExecutionPolicy Bypass -File scripts/run_runtime.ps1`
- Start API runtime (Ubuntu/macOS): `bash scripts/run_runtime.sh`
- Submit objective to orchestrator: `POST /runs` with `X-Tenant-Id` and `X-Api-Key`
- Track progression: `GET /runs` and `GET /runs/{run_id}/tasks`
- Inspect failures: `GET /runs/{run_id}/dead-letter`
- Query persisted context at any point: `GET /memory/search?query=<term>`

## Implementation Notes
- Delegation is code-driven through `runtime/agent_runtime/engine.py` dependency graph scheduling.
- Workers process queue jobs concurrently, retry failed tasks, and move exhausted tasks to dead-letter.
- Specialist execution is LLM-backed when provider environment variables are configured.
- Run, task, and memory visibility are tenant-isolated via API key auth.

