from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib import error, request

from .prompt_assets import load_role_prompt
from .models import TaskRecord, TaskType
from .output_contracts import extract_agent_json_block, summarize_narrative, validate_agent_payload


class LLMClient:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.base_url = os.getenv("AGENT_LLM_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("AGENT_LLM_API_KEY", "")
        self.model = os.getenv("AGENT_LLM_MODEL", "gpt-4o-mini")
        self.timeout = int(os.getenv("AGENT_LLM_TIMEOUT", "45"))

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def generate_worker_output(self, task: TaskRecord) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("LLM client is not configured")

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(task),
                },
                {
                    "role": "user",
                    "content": self._user_prompt(task),
                },
            ],
            "temperature": 0.2,
        }

        req = request.Request(
            url=f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM HTTP error {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"LLM connection error: {exc.reason}") from exc

        message = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        if not isinstance(message, str):
            raise RuntimeError("LLM returned unsupported message format")

        # Backward-compatible fallback for prompt enhancement tasks that still return JSON-only payloads.
        if task.task_type == TaskType.PROMPT_ENHANCE:
            try:
                parsed = json.loads(message)
                if isinstance(parsed, dict) and "summary" in parsed and "artifacts" in parsed:
                    summary = str(parsed.get("summary", "No summary"))
                    artifacts = parsed.get("artifacts", {})
                    if not isinstance(artifacts, dict):
                        artifacts = {"raw_artifacts": artifacts}
                    artifacts["contract_validation"] = "skipped_prompt_enhance"
                    artifacts["raw_response"] = message
                    return {"summary": summary, "artifacts": artifacts, "mode": "llm"}
            except json.JSONDecodeError:
                pass

        try:
            agent_payload = extract_agent_json_block(message)
        except ValueError as exc:
            raise RuntimeError(f"Missing or invalid machine-readable output: {exc}") from exc

        validation_errors = validate_agent_payload(task.role, agent_payload)
        if validation_errors:
            joined = "; ".join(validation_errors)
            raise RuntimeError(f"Agent output schema validation failed: {joined}")

        summary = summarize_narrative(message)
        artifacts = {
            "agent_json": agent_payload,
            "raw_response": message,
            "contract_validation": "passed",
        }
        return {"summary": summary, "artifacts": artifacts, "mode": "llm"}

    def _system_prompt(self, task: TaskRecord) -> str:
        if task.task_type == TaskType.PROMPT_ENHANCE:
            return (
                "You are a specialist software delivery agent improving prompts. "
                "Return strict JSON only with keys: summary (string), artifacts (object). "
                "artifacts must include enhanced_prompt (string), target_file (string), and title (string)."
            )

        role_prompt = load_role_prompt(self.repo_root, task.role)
        return (
            "You are a specialist software delivery agent. "
            f"Current role: {task.role.value}. "
            "Follow the role prompt exactly. Produce a concise narrative, then include exactly one machine-readable JSON block enclosed by BEGIN_AGENT_JSON and END_AGENT_JSON. "
            "The JSON block must match the role schema in the role prompt.\n\n"
            f"Role prompt reference:\n{role_prompt}"
        )

    def _user_prompt(self, task: TaskRecord) -> str:
        payload_text = json.dumps(task.payload, ensure_ascii=True)
        return (
            f"Objective: {task.objective}\n"
            f"Task type: {task.task_type.value}\n"
            f"Role: {task.role.value}\n"
            f"Payload: {payload_text}\n"
            "Provide concise implementation-ready output."
        )
