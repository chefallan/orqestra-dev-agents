# orqestra-dev-agents

Installable CLI to bootstrap an orchestrator-driven autonomous agent setup for repositories operated from Copilot, Claude, Codex, OpenCode, and similar coding assistants.

## Install

```bash
npm install -D orqestra-dev-agents
```

Or one-off with npx:

```bash
npx orqestra-dev-agents init
```

## Quick Onboarding (Recommended)

Run these commands inside your target repository:

```bash
npm install -D orqestra-dev-agents@latest
npx orqestra-dev-agents init --with-runtime --with-contracts
npx orqestra-dev-agents doctor --with-runtime --with-contracts
npx orqestra-dev-agents install-vscode
```

Note: if `package.json` is missing, `init` now creates a minimal one automatically and wires runtime scripts.

Then in your coding assistant:

1. In GitHub Copilot Chat, open Agent mode and select the Orqestra chat mode.
2. In Claude, Codex, OpenCode, and similar assistants, start from `AGENTS.md` or `.github/skills/orqestra-workflow/SKILL.md`.
3. Use `agents/orchestrator.agents.md` as the direct entrypoint agent spec when your assistant supports loading prompt files.
	- If `.github/copilot-instructions.md` exists, Copilot can directly talk to the orchestrator without manual spec paste.
4. Start with a concrete objective, for example:

```text
Build the first production-ready vertical slice for user signup, login, and project creation with tests.
```

Recommended autonomous mode before prompting:

```bash
npm run orqestra:start
```

## Commands

### Compact daily-use hub

Open the compact catalog for the current repo and your available skills:

```bash
orqestra-dev-agents hub
```

List or open agent specs:

```bash
orqestra-dev-agents agents
orqestra-dev-agents agents orchestrator
orqestra-dev-agents agents orchestrator --print
```

List or open workflows:

```bash
orqestra-dev-agents workflows
orqestra-dev-agents workflows autonomous-webapp-loop
```

List or open contracts and tickets:

```bash
orqestra-dev-agents contracts
orqestra-dev-agents contracts handoff-contract
```

List or open skills:

```bash
orqestra-dev-agents skills
orqestra-dev-agents skills georithm
orqestra-dev-agents skills agents
orqestra-dev-agents skills install orqestra-workflow --agent claude-code --scope project
```

Skills are resolved from these directories when present:

- `skills/` in the current repo
- `.agents/skills/` in the current repo
- `.github/skills/` in the current repo
- `~/.claude/skills/`
- any extra paths in `ORQESTRA_SKILLS_DIRS` separated by your platform path delimiter

The package scaffolds a repo-local skill at `.github/skills/orqestra-workflow/SKILL.md` so non-Copilot assistants have a first-class Orqestra entrypoint too.

The CLI can also install skills into supported agent-specific directories for project or global scope. Use `orqestra-dev-agents skills agents` to list the full registry. Supported ids include `amp`, `augment`, `claude-code`, `cline`, `codex`, `continue`, `cursor`, `gemini-cli`, `github-copilot`, `opencode`, `roo`, `windsurf`, `zencoder`, and the rest of the registry you provided.

Examples:

```bash
orqestra-dev-agents skills agents
orqestra-dev-agents skills install orqestra-workflow --agent claude-code --scope project
orqestra-dev-agents skills install orqestra-workflow --agent codex --scope project
orqestra-dev-agents skills install orqestra-workflow --agent github-copilot --scope global
```

Run related tools from one command surface:

```bash
orqestra-dev-agents tools
orqestra-dev-agents tools handoff --from orchestrator --to webapp-builder --epic compact-cli
orqestra-dev-agents tools memory search --query "runtime"
orqestra-dev-agents tools validate-contracts
```

### Initialize a repo

```bash
orqestra-dev-agents init
```

Initialize in a specific directory:

```bash
orqestra-dev-agents init ../my-repo
```

Overwrite existing files:

```bash
orqestra-dev-agents init --force
```

Initialize only core files (agent specs + workflow + config):

```bash
orqestra-dev-agents init --minimal
```

Initialize with runtime, scripts, templates, and requirements:

```bash
orqestra-dev-agents init --with-runtime
```

Initialize with agent contracts and handoff template:

```bash
orqestra-dev-agents init --with-contracts
```

### Validate required files

```bash
orqestra-dev-agents doctor
```

Validate only minimal mode requirements:

```bash
orqestra-dev-agents doctor --minimal
```

Validate runtime and contracts are present:

```bash
orqestra-dev-agents doctor --with-runtime --with-contracts
```

### Show guided onboarding steps

```bash
orqestra-dev-agents onboarding
```

### Install VS Code dependencies

Install required VS Code extensions for this workflow:

```bash
orqestra-dev-agents install-vscode
```

Check only (no install):

```bash
orqestra-dev-agents install-vscode --check
```

### Runtime start/stop/status (single command)

After init with runtime assets, the CLI auto-adds npm scripts to your target `package.json`:

```bash
npm run orqestra:hub
npm run orqestra:agents
npm run orqestra:workflows
npm run orqestra:skills
npm run orqestra:tools
npm run orqestra:start
npm run orqestra:status
npm run orqestra:stop
npm run orqestra:progress
npm run orqestra:doctor
```

Note: `npm run orqestra:start` now starts the runtime and then opens live progress watch.

Direct CLI usage (single snapshot):

```bash
orqestra-dev-agents runtime progress
```

Direct CLI usage (live watch):

```bash
orqestra-dev-agents runtime progress --watch
```

Compatibility command (also added when available):

```bash
npm run runtime -- start
```

Optional custom port:

```bash
npm run runtime -- start --port 8090
```

Behavior:

- Before `start`, CLI checks Python availability (`python` or `python3`).
- It verifies runtime dependencies (`fastapi`, `uvicorn`, `pydantic`) and installs from `requirements.txt` if missing.
- It initializes memory DB (`scripts/memory_cli.py init`) and starts runtime in the background.
- It stores process id in `.orqestra-runtime.pid` for stop/status operations.

## One Prompt Automation Build

Use this when you want the orchestrator to drive end-to-end automation from one prompt:

```text
Build and automate a production-ready MVP with signup/login, project creation, tests, docs updates, and memory snapshots. Execute in thin vertical slices until a releasable first version is ready, and report progress after each slice.
```

Suggested flow:

1. Install VS Code dependencies: `orqestra-dev-agents install-vscode`
2. Start runtime + live watch: `npm run orqestra:start`
3. Open your coding assistant of choice.
4. Use `AGENTS.md`, `.github/skills/orqestra-workflow/SKILL.md`, or `agents/orchestrator.agents.md` depending on what the assistant supports.
5. Send the single objective above in chat.
6. Track runtime status anytime with `npm run orqestra:status`.
7. Stop runtime when done with `npm run orqestra:stop`.

## Generated assets

- `agents/*` specialist agent specs
- `agents/workflows/autonomous-webapp-loop.md`
- `agents/memory/context-ledger.md`
- `agents/memory/decision-log.md`
- `agents/memory/memory-schema.sql`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/skills/orqestra-workflow/SKILL.md`
- `docs/autogenerated/ARCHITECTURE.md`
- `docs/autogenerated/CHANGES.md`
- `orqestra-dev-agents.agents.json` config

With `--with-runtime`, generated scripts include both Windows and Unix shells:

- `scripts/run_runtime.ps1` and `scripts/run_runtime.sh`
- `scripts/new_handoff_ticket.ps1` and `scripts/new_handoff_ticket.sh`

## Troubleshooting

If `orqestra-dev-agents --version` works but you do not see generated files, the CLI is installed but initialization has not run in your current project directory yet.

Run:

```bash
orqestra-dev-agents init
orqestra-dev-agents doctor
```

If files already exist and you want to overwrite them:

```bash
orqestra-dev-agents init --force
```

