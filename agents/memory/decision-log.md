# Decision Log

Record architectural and product decisions in ADR style.

## Template
- Date:
- Decision:
- Context:
- Options considered:
- Selected option:
- Consequences:
- Owner:
- Related ticket:

## Entries
- Date: 2026-04-18
	Decision: Inject a default scaffold context into runtime-created runs and standardize build defaults to `app/api`, `app/web`, and `app/docs`.
	Context: Users observed agent-driven build output drifting into Orqestra runtime paths (especially `runtime/`) and wanted a stable default app layout with opt-in custom directories.
	Options considered: document preferred paths only; hard-fail any non-app path; set default paths in run context while allowing explicit overrides.
	Selected option: set default paths in run context while allowing explicit overrides.
	Consequences: downstream agent tasks receive explicit app-first directory defaults while advanced users can still request custom locations.
	Owner: orchestrator
	Related ticket: Runtime scaffold default policy

- Date: 2026-04-18
	Decision: Clarify CLI runtime progress output when no runs exist to distinguish plain chat sessions from tracked runtime runs.
	Context: The message "No runs found yet" was interpreted as a malfunction after long chat sessions in Copilot.
	Options considered: keep message unchanged; auto-create runs from any chat message; improve message and keep API-driven run model.
	Selected option: improve message and keep API-driven run model.
	Consequences: less confusion about runtime telemetry boundaries without changing runtime semantics.
	Owner: orchestrator
	Related ticket: Runtime progress UX clarity

- Date: 2026-04-18
	Decision: Replace runtime annotation syntax with Python 3.8-safe typing aliases across runtime source and packaged runtime assets.
	Context: Runtime models and APIs used `dict[str, ...]`, `list[...]`, and `X | None`, which can fail when frameworks evaluate type hints on older interpreters.
	Options considered: keep modern annotations with backport dependency; move to conservative typing aliases; remove most type hints.
	Selected option: move to conservative typing aliases (`Dict`, `List`, `Optional`, `Tuple`, `Set`) while keeping type hints.
	Consequences: broader interpreter compatibility and fewer annotation-evaluation surprises while preserving readability and static typing intent.
	Owner: orchestrator
	Related ticket: Python runtime compatibility hardening

- Date: 2026-04-18
	Decision: Set runtime CLI Python minimum to 3.8+ and remove `eval-type-backport` from requirements and import checks.
	Context: Backport package was originally added to support evaluated `X | None` hints, but the runtime compatibility rewrite removed that requirement.
	Options considered: keep 3.9+ gate with backport; keep backport but lower gate; lower gate and remove backport.
	Selected option: lower gate and remove backport.
	Consequences: simpler dependency graph and better compatibility alignment with FastAPI/Pydantic baseline support.
	Owner: orchestrator
	Related ticket: Python runtime compatibility hardening

- Date: 2026-04-18
	Decision: Support a registry of agent-specific skill paths and expose `skills agents` plus `skills install` in the CLI.
	Context: Portable Orqestra skills existed, but users still needed to know each agent's project/global skill directory and copy files by hand.
	Options considered: document the path matrix only; auto-generate all agent folders in every repo; keep one source skill and add an installer backed by a supported-agent registry.
	Selected option: keep one source skill and add an installer backed by a supported-agent registry.
	Consequences: avoids cluttering repos with dozens of agent folders while making supported installs explicit and scriptable for the agent ecosystems you listed.
	Owner: orchestrator
	Related ticket: Supported skill agent registry

- Date: 2026-04-18
	Decision: Add portable assistant entrypoints with AGENTS.md and a repo-local Orqestra workflow skill.
	Context: The package and docs were biased toward Copilot-specific entrypoints, which made Claude, Codex, OpenCode, and similar assistants second-class even though the underlying workflow is markdown-based.
	Options considered: keep Copilot-only entrypoints; add only documentation notes; add assistant-agnostic workspace instructions and a packaged skill alongside the Copilot files.
	Selected option: add assistant-agnostic workspace instructions and a packaged skill alongside the Copilot files.
	Consequences: preserves the best Copilot experience while giving other assistants a standard entrypoint that can be scaffolded into downstream repositories.
	Owner: orchestrator
	Related ticket: Multi-assistant compatibility update

- Date: 2026-04-18
	Decision: Add a hub-style CLI layer for discovery and launch instead of expanding the existing init/runtime flags.
	Context: The package already scaffolds repos and manages runtime, but daily work still requires manual navigation across agent specs, workflows, contracts, and scripts.
	Options considered: extend the current top-level flags only; build a separate interactive TUI; add catalog-style commands on top of the current CLI.
	Selected option: add catalog-style commands on top of the current CLI.
	Consequences: improves discoverability and one-command access with minimal migration cost, while keeping the current scaffold and runtime flows stable.
	Owner: orchestrator
	Related ticket: CLI compact access update
