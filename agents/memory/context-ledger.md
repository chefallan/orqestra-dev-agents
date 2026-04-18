# Context Ledger

Purpose: durable memory for project state that specialists can reuse.

## Active Objective
- Improve runtime UX clarity and enforce default app scaffold paths for agent-built projects.

## Current Phase
- Runtime UX and scaffold policy hardening

## Decisions (Newest First)
- 2026-04-18: Bumped package version to 1.0.0 (major) and validated publish tarball; npm publish blocked by registry auth on current machine | reason: user requested immediate major release publish | impact: release is ready to publish once npm login is completed (`npm adduser` or `npm login`)
- 2026-04-18: Expanded init `.gitignore` defaults with framework/tool cache ignores (Next.js, Nuxt, SvelteKit, Turbo, TS build cache, Python tox/nox) | reason: reduce noisy git status and accidental cache commits across common stacks | impact: scaffolded repos have cleaner defaults for multi-stack projects
- 2026-04-18: Added default `.gitignore` generation on init (full and minimal) with baseline Node/Python/runtime ignores | reason: prevent common local/build/runtime artifacts from entering git by default | impact: newly scaffolded repos now include `.gitignore` without manual setup
- 2026-04-18: Added runtime run-tracking clarification in CLI progress output | reason: users expected normal Copilot chat history to appear in runtime runs | impact: progress output now clearly states that plain chat is not auto-tracked and that POST /runs creates tracked runs
- 2026-04-18: Enforced default scaffold context for runtime-created runs (`app/api`, `app/web`, `app/docs`) while preserving custom-path override | reason: avoid accidental product code generation into `runtime/` and provide predictable default layout | impact: orchestration payload context now carries explicit default build paths for downstream agents
- 2026-04-18: Updated orchestrator and webapp-builder specs plus templates to treat `runtime/` as Orqestra runtime files only and default product code to `app/` | reason: align live behavior and scaffolded repo instructions | impact: both existing and newly scaffolded repos follow the same default path policy
- 2026-04-18: Rewrote runtime type hints from PEP 585/604 forms to Python 3.8-safe typing aliases (`Dict`, `List`, `Optional`, etc.) in both source and packaged runtime trees | reason: remove runtime failures from evaluated annotations on older Python interpreters | impact: reduces dependency on annotation backports and broadens interpreter compatibility
- 2026-04-18: Lowered CLI Python gate to 3.8+ and removed `eval-type-backport` requirement checks | reason: compatibility rewrite removed the need for backport-based union evaluation | impact: runtime start checks now align with broader Python support goals
- 2026-04-18: Added a supported-agent skill registry plus `skills agents` and `skills install` commands | reason: make Orqestra skills installable into the project/global skill paths used by major coding agents | impact: package users can target agent-specific skill directories such as Claude Code, Codex, Cursor, Continue, OpenCode, Copilot, and the full supported registry
- 2026-04-18: Added portable assistant entrypoints via `AGENTS.md` and `.github/skills/orqestra-workflow/SKILL.md` | reason: make the same orchestrator workflow usable from Copilot, Claude, Codex, OpenCode, and similar assistants | impact: scaffolded repos now ship both Copilot-specific and assistant-agnostic entry surfaces
- 2026-04-18: Added hub-style catalog commands (`hub`, `agents`, `workflows`, `skills`, `contracts`, `tools`) to the package CLI | reason: improve day-to-day discoverability and one-command launch paths without replacing scaffold/runtime flows | impact: package users can list, open, print, and run core Orqestra assets faster

## Open Risks
- <risk> | owner: <agent> | mitigation: <step>

## Completed Milestones
- Runtime compatibility rewrite validated via compile checks and runtime start/status/stop smoke test on local Python | evidence: `python3 -m compileall runtime packages/orqestra-dev-agents/assets/runtime` and CLI runtime lifecycle commands
- Compact CLI surface implemented in `packages/orqestra-dev-agents/src/cli.js` | evidence: local CLI help and catalog command verification
- npm aliases and portable assistant assets added to the scaffold templates | evidence: template updates for `AGENTS.md`, skill scaffolding, and alias scripts
- Supported-agent skill registry and installer added for project/global agent paths | evidence: `skills agents` output and temporary repo install verification

## Retrieval Notes
- Keep entries factual and concise.
- Link to source files and tickets.
