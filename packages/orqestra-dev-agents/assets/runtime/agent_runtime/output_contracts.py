from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from .models import AgentRole


_MARKER_PATTERN = re.compile(r"BEGIN_AGENT_JSON\s*(\{.*?\})\s*END_AGENT_JSON", re.DOTALL)


def extract_agent_json_block(text: str) -> dict[str, Any]:
    match = _MARKER_PATTERN.search(text)
    if not match:
        raise ValueError("Missing BEGIN_AGENT_JSON/END_AGENT_JSON block")
    block = match.group(1)
    try:
        parsed = json.loads(block)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in agent block: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Agent JSON block must be an object")
    return parsed


def summarize_narrative(text: str) -> str:
    marker_index = text.find("BEGIN_AGENT_JSON")
    narrative = text[:marker_index].strip() if marker_index >= 0 else text.strip()
    if not narrative:
        return "No narrative summary provided."
    first_line = next((line.strip() for line in narrative.splitlines() if line.strip()), "")
    return first_line or "No narrative summary provided."


def validate_agent_payload(role: AgentRole, payload: dict[str, Any]) -> list[str]:
    schema = _ROLE_SCHEMAS.get(role)
    if not schema:
        return []
    errors: list[str] = []
    _validate_value(payload, schema, path="$", errors=errors)
    return errors


def get_role_schema(role: AgentRole) -> dict[str, Any] | None:
    schema = _ROLE_SCHEMAS.get(role)
    return deepcopy(schema) if schema else None


def get_role_schemas() -> dict[AgentRole, dict[str, Any]]:
    return {role: deepcopy(schema) for role, schema in _ROLE_SCHEMAS.items()}


def _validate_value(value: Any, schema: dict[str, Any], *, path: str, errors: list[str]) -> None:
    expected_type = schema.get("type")
    if expected_type == "str":
        if not isinstance(value, str):
            errors.append(f"{path} must be a string")
        return

    if expected_type == "enum":
        values = schema.get("values", [])
        if not isinstance(value, str) or value not in values:
            errors.append(f"{path} must be one of: {', '.join(values)}")
        return

    if expected_type == "dict":
        if not isinstance(value, dict):
            errors.append(f"{path} must be an object")
            return
        fields: dict[str, dict[str, Any]] = schema.get("fields", {})
        required: list[str] = schema.get("required", list(fields.keys()))
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key} is required")
        for key, field_schema in fields.items():
            if key in value:
                _validate_value(value[key], field_schema, path=f"{path}.{key}", errors=errors)
        return

    if expected_type == "list":
        if not isinstance(value, list):
            errors.append(f"{path} must be an array")
            return
        item_schema = schema.get("item")
        if not item_schema:
            return
        for index, item in enumerate(value):
            _validate_value(item, item_schema, path=f"{path}[{index}]", errors=errors)
        return

    errors.append(f"{path} has unsupported schema type: {expected_type}")


_ROLE_SCHEMAS: dict[AgentRole, dict[str, Any]] = {
    AgentRole.ORCHESTRATOR: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["orchestrator"]},
            "objective": {"type": "str"},
            "phase": {
                "type": "enum",
                "values": [
                    "intake",
                    "product",
                    "architecture",
                    "build",
                    "security",
                    "qa",
                    "documentation",
                    "memory",
                    "report",
                ],
            },
            "active_slice": {"type": "str"},
            "delegations": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "to": {"type": "str"},
                        "ticket": {"type": "str"},
                        "status": {
                            "type": "enum",
                            "values": ["planned", "in_progress", "completed", "blocked"],
                        },
                    },
                },
            },
            "verified_findings": {"type": "list", "item": {"type": "str"}},
            "assumptions": {"type": "list", "item": {"type": "str"}},
            "next_action": {"type": "str"},
            "risks": {"type": "list", "item": {"type": "str"}},
        },
    },
    AgentRole.PRODUCT_MANAGER: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["product_manager"]},
            "problem_statement": {"type": "str"},
            "users": {"type": "list", "item": {"type": "str"}},
            "stories": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "id": {"type": "str"},
                        "title": {"type": "str"},
                        "priority": {"type": "enum", "values": ["P0", "P1", "P2"]},
                        "dependencies": {"type": "list", "item": {"type": "str"}},
                        "acceptance_criteria": {"type": "list", "item": {"type": "str"}},
                    },
                },
            },
            "scope_in": {"type": "list", "item": {"type": "str"}},
            "scope_out": {"type": "list", "item": {"type": "str"}},
            "risks": {"type": "list", "item": {"type": "str"}},
            "assumptions": {"type": "list", "item": {"type": "str"}},
            "open_questions": {"type": "list", "item": {"type": "str"}},
        },
    },
    AgentRole.SYSTEM_ARCHITECT: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["system_architect"]},
            "stack_profile": {
                "type": "dict",
                "fields": {
                    "frontend": {"type": "str"},
                    "backend": {"type": "str"},
                    "assumptions": {"type": "list", "item": {"type": "str"}},
                },
            },
            "adrs": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "id": {"type": "str"},
                        "decision": {"type": "str"},
                        "rationale": {"type": "str"},
                        "tradeoffs": {"type": "list", "item": {"type": "str"}},
                    },
                },
            },
            "contracts": {
                "type": "dict",
                "fields": {
                    "api": {"type": "list", "item": {"type": "str"}},
                    "schema": {"type": "list", "item": {"type": "str"}},
                    "events": {"type": "list", "item": {"type": "str"}},
                },
            },
            "operational_controls": {"type": "list", "item": {"type": "str"}},
            "handoff_notes": {"type": "list", "item": {"type": "str"}},
            "risks": {"type": "list", "item": {"type": "str"}},
        },
    },
    AgentRole.WEBAPP_BUILDER: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["webapp_builder"]},
            "slice": {
                "type": "dict",
                "fields": {
                    "title": {"type": "str"},
                    "objective": {"type": "str"},
                },
            },
            "stack_profile": {
                "type": "dict",
                "fields": {
                    "frontend": {"type": "str"},
                    "backend": {"type": "str"},
                },
            },
            "files_changed": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "path": {"type": "str"},
                        "purpose": {"type": "str"},
                    },
                },
            },
            "acceptance_criteria": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "id": {"type": "str"},
                        "status": {"type": "enum", "values": ["pass", "fail", "blocked"]},
                        "evidence": {"type": "str"},
                    },
                },
            },
            "validation": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "command": {"type": "str"},
                        "result": {"type": "enum", "values": ["pass", "fail"]},
                        "notes": {"type": "str"},
                    },
                },
            },
            "contract_checks": {"type": "list", "item": {"type": "str"}},
            "frontend_checks": {"type": "list", "item": {"type": "str"}},
            "backend_checks": {"type": "list", "item": {"type": "str"}},
            "risks": {"type": "list", "item": {"type": "str"}},
            "follow_ups": {"type": "list", "item": {"type": "str"}},
            "rollback_notes": {"type": "list", "item": {"type": "str"}},
        },
    },
    AgentRole.SECURITY_AUDITOR: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["security_auditor"]},
            "findings": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "id": {"type": "str"},
                        "severity": {
                            "type": "enum",
                            "values": ["critical", "high", "medium", "low"],
                        },
                        "component": {"type": "str"},
                        "exploitability": {"type": "enum", "values": ["high", "medium", "low"]},
                        "evidence": {"type": "str"},
                        "fix": {"type": "str"},
                    },
                },
            },
            "immediate_actions": {"type": "list", "item": {"type": "str"}},
            "backlog_actions": {"type": "list", "item": {"type": "str"}},
            "validation_steps": {"type": "list", "item": {"type": "str"}},
            "recommendation": {"type": "enum", "values": ["pass", "hold"]},
            "gate_reason": {"type": "str"},
        },
    },
    AgentRole.QA_RELIABILITY: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["qa_reliability"]},
            "ac_verification": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "id": {"type": "str"},
                        "status": {"type": "enum", "values": ["pass", "fail", "blocked"]},
                        "evidence": {"type": "str"},
                    },
                },
            },
            "defects": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "id": {"type": "str"},
                        "severity": {
                            "type": "enum",
                            "values": ["critical", "high", "medium", "low"],
                        },
                        "repro": {"type": "str"},
                        "impact": {"type": "str"},
                    },
                },
            },
            "regression_risks": {"type": "list", "item": {"type": "str"}},
            "recommendation": {"type": "enum", "values": ["ship", "hold"]},
            "rationale": {"type": "str"},
        },
    },
    AgentRole.DOCUMENTATION_AGENT: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["documentation_agent"]},
            "files_updated": {"type": "list", "item": {"type": "str"}},
            "architecture_deltas": {
                "type": "list",
                "item": {
                    "type": "dict",
                    "fields": {
                        "what": {"type": "str"},
                        "why": {"type": "str"},
                        "impact": {"type": "str"},
                        "source": {"type": "str"},
                    },
                },
            },
            "change_log_entries": {"type": "list", "item": {"type": "str"}},
            "known_gaps": {"type": "list", "item": {"type": "str"}},
        },
    },
    AgentRole.MEMORY_STEWARD: {
        "type": "dict",
        "fields": {
            "agent": {"type": "enum", "values": ["memory_steward"]},
            "artifacts_updated": {"type": "list", "item": {"type": "str"}},
            "decisions_recorded": {"type": "list", "item": {"type": "str"}},
            "conflicts": {"type": "list", "item": {"type": "str"}},
            "retrieval_snippets": {"type": "list", "item": {"type": "str"}},
        },
    },
}
