from __future__ import annotations

from typing import Dict

from pathlib import Path

from .models import AgentRole

ROLE_PROMPT_FILES: Dict[AgentRole, str] = {
    AgentRole.ORCHESTRATOR: "orchestrator.agents.md",
    AgentRole.PRODUCT_MANAGER: "product-manager.agents.md",
    AgentRole.SYSTEM_ARCHITECT: "system-architect.agents.md",
    AgentRole.WEBAPP_BUILDER: "webapp-builder.agents.md",
    AgentRole.SECURITY_AUDITOR: "security-auditor.agents.md",
    AgentRole.QA_RELIABILITY: "qa-reliability.agents.md",
    AgentRole.DOCUMENTATION_AGENT: "documentation-agent.agents.md",
    AgentRole.MEMORY_STEWARD: "memory-steward.agents.md",
}


def load_role_prompt(repo_root: Path, role: AgentRole) -> str:
    file_name = ROLE_PROMPT_FILES.get(role, "")
    if not file_name:
        return ""
    agent_path = repo_root / "agents" / file_name
    if agent_path.exists():
        return agent_path.read_text(encoding="utf-8")

    # Backward compatibility for existing repositories not yet migrated.
    legacy_file_name = file_name.replace(".agents.md", ".prompt.md")
    legacy_path = repo_root / ".github" / "prompts" / legacy_file_name
    if legacy_path.exists():
        return legacy_path.read_text(encoding="utf-8")
    return ""
