---
name: orqestra-workflow
description: "Use when running the Orqestra orchestrator workflow from Copilot, Claude, Codex, OpenCode, or another coding assistant. Covers intake, phased planning, thin-slice delegation, contracts, validation, docs, and memory updates."
---

# Orqestra Workflow Skill

Use this skill when the user wants the Orqestra system to drive work through the orchestrator and specialist agents.

## Entry files

- AGENTS.md
- agents/orchestrator.agents.md
- agents/contracts/handoff-contract.md
- agents/workflows/autonomous-webapp-loop.md
- agents/memory/context-ledger.md
- agents/memory/decision-log.md

## Workflow

1. Restate the objective in one sentence.
2. Build a phased plan before implementation.
3. Keep work in thin, end-to-end vertical slices.
4. Delegate using agents/contracts/handoff-contract.md.
5. Require evidence for implementation, QA, security, documentation, and memory updates.
6. Update context-ledger and decision-log after major changes.
7. Report blockers early with one recommended path.

## Specialist map

- Product framing: agents/product-manager.agents.md
- Architecture: agents/system-architect.agents.md
- Implementation: agents/webapp-builder.agents.md
- Security: agents/security-auditor.agents.md
- QA and reliability: agents/qa-reliability.agents.md
- Documentation: agents/documentation-agent.agents.md
- Memory stewardship: agents/memory-steward.agents.md

## Compatibility notes

- GitHub Copilot Chat can also use .github/copilot-instructions.md and the Orqestra chat mode.
- Claude, Codex, OpenCode, and similar assistants should treat this skill plus AGENTS.md as the default operating contract for the repo.
- If the assistant does not support skills, load AGENTS.md and agents/orchestrator.agents.md directly.
