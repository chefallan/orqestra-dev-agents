from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.agent_runtime.models import AgentRole
from runtime.agent_runtime.output_contracts import get_role_schemas
from runtime.agent_runtime.prompt_assets import ROLE_PROMPT_FILES


def _find_schema_json_block(text: str) -> dict[str, Any]:
    marker = "- JSON schema:"
    marker_index = text.find(marker)
    if marker_index < 0:
        raise ValueError("Missing '- JSON schema:' section")

    start = text.find("{", marker_index)
    if start < 0:
        raise ValueError("JSON schema block start '{' not found")

    depth = 0
    end = -1
    for idx in range(start, len(text)):
        char = text[idx]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = idx + 1
                break

    if end < 0:
        raise ValueError("JSON schema block end '}' not found")

    block = text[start:end]
    try:
        parsed = json.loads(block)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON schema block: {exc}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("JSON schema block must be an object")

    return parsed


def _check_enum(value: Any, expected_values: list[str], path: str, errors: list[str]) -> None:
    if not isinstance(value, str):
        errors.append(f"{path}: enum placeholder must be a string")
        return
    declared = [part.strip() for part in value.split("|") if part.strip()]
    if set(declared) != set(expected_values):
        errors.append(
            f"{path}: enum mismatch. prompt={declared} runtime={expected_values}"
        )


def _check_schema(prompt_value: Any, runtime_schema: dict[str, Any], path: str, errors: list[str]) -> None:
    schema_type = runtime_schema.get("type")

    if schema_type == "str":
        if prompt_value != "string":
            errors.append(f"{path}: expected 'string' placeholder")
        return

    if schema_type == "enum":
        _check_enum(prompt_value, runtime_schema.get("values", []), path, errors)
        return

    if schema_type == "list":
        if not isinstance(prompt_value, list):
            errors.append(f"{path}: expected an array schema example")
            return
        if len(prompt_value) != 1:
            errors.append(f"{path}: array schema should contain exactly one exemplar item")
            return
        item_schema = runtime_schema.get("item")
        if not isinstance(item_schema, dict):
            return
        _check_schema(prompt_value[0], item_schema, f"{path}[0]", errors)
        return

    if schema_type == "dict":
        if not isinstance(prompt_value, dict):
            errors.append(f"{path}: expected an object schema example")
            return

        runtime_fields: dict[str, dict[str, Any]] = runtime_schema.get("fields", {})
        prompt_keys = set(prompt_value.keys())
        runtime_keys = set(runtime_fields.keys())

        missing = sorted(runtime_keys - prompt_keys)
        extra = sorted(prompt_keys - runtime_keys)
        if missing:
            errors.append(f"{path}: missing keys in prompt schema: {missing}")
        if extra:
            errors.append(f"{path}: extra keys in prompt schema: {extra}")

        for key, field_schema in runtime_fields.items():
            if key in prompt_value:
                _check_schema(prompt_value[key], field_schema, f"{path}.{key}", errors)
        return

    errors.append(f"{path}: unsupported runtime schema type '{schema_type}'")


def validate_prompt_file(prompt_path: Path, role: AgentRole, runtime_schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    text = prompt_path.read_text(encoding="utf-8")

    try:
        prompt_schema = _find_schema_json_block(text)
    except ValueError as exc:
        return [f"{prompt_path}: {exc}"]

    _check_schema(prompt_schema, runtime_schema, path="$", errors=errors)

    return [f"{prompt_path}: {error}" for error in errors]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate agent-spec JSON schemas against runtime contract schemas."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root path (default: current directory)",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    prompt_root = repo_root / "agents"

    if not prompt_root.exists():
        print(f"Agent specs directory not found: {prompt_root}")
        return 2

    runtime_schemas = get_role_schemas()

    all_errors: list[str] = []
    checked = 0

    for role, file_name in ROLE_PROMPT_FILES.items():
        prompt_path = prompt_root / file_name
        if not prompt_path.exists():
            all_errors.append(f"{prompt_path}: agent spec file missing")
            continue

        runtime_schema = runtime_schemas.get(role)
        if not runtime_schema:
            all_errors.append(f"{prompt_path}: runtime schema missing for role {role.value}")
            continue

        checked += 1
        all_errors.extend(validate_prompt_file(prompt_path, role, runtime_schema))

    if all_errors:
        print("Agent schema drift detected:")
        for err in all_errors:
            print(f"- {err}")
        print(f"\nChecked {checked} agent spec files. Found {len(all_errors)} issues.")
        return 1

    print(f"Agent spec schemas are aligned with runtime contracts. Checked {checked} agent spec files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
