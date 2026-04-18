# Orqestra Workspace Instructions

Use Orchestrator behavior by default for this workspace, regardless of which coding assistant you are using.

Primary entrypoints:
- AGENTS.md for assistants that automatically read workspace instructions.
- .github/copilot-instructions.md for GitHub Copilot Chat.
- .github/skills/orqestra-workflow/SKILL.md for assistants that expose reusable skills.
- agents/orchestrator.agents.md for direct prompt or agent-spec loading.

Operating requirements:
- Restate the objective clearly and build a phased plan.
- Delegate by creating or using contracts under agents/contracts/.
- Keep delivery in thin, end-to-end slices with validation evidence.
- Keep memory updated in agents/memory/context-ledger.md and decision-log.md.
- Prefer progress updates and the next best action after each major step.

Specialist agent specs:
- agents/product-manager.agents.md
- agents/system-architect.agents.md
- agents/webapp-builder.agents.md
- agents/security-auditor.agents.md
- agents/qa-reliability.agents.md
- agents/documentation-agent.agents.md
- agents/memory-steward.agents.md

Assistant compatibility notes:
- GitHub Copilot Chat: use .github/copilot-instructions.md and .github/chatmodes/orqestra-orchestrator.chatmode.md.
- Claude, Codex, OpenCode, and similar assistants: start from this file, then use agents/orchestrator.agents.md plus the handoff contract and workflow files.
- Skills-capable assistants: load .github/skills/orqestra-workflow/SKILL.md for the packaged workflow.
