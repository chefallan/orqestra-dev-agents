from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .auth import load_api_key_map
from .docs_store import DocsStore
from .llm import LLMClient
from .memory import MemoryStore
from .models import AgentRole, RunView, TaskRecord, TaskStatus, TaskType
from .prompt_store import PromptStore
from .store import TaskStore
from .workers import execute_specialist


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _contract_validation_summary(task: TaskRecord) -> dict:
    status = "not_applicable"
    valid: bool | None = None
    errors: list[str] = []

    artifacts = {}
    if isinstance(task.output, dict):
        output_artifacts = task.output.get("artifacts", {})
        if isinstance(output_artifacts, dict):
            artifacts = output_artifacts

    contract_flag = artifacts.get("contract_validation")
    if contract_flag == "passed":
        status = "passed"
        valid = True
    elif contract_flag == "skipped_prompt_enhance":
        status = "skipped"
    elif isinstance(contract_flag, str) and contract_flag:
        status = contract_flag

    contract_errors = artifacts.get("contract_errors")
    if isinstance(contract_errors, list):
        errors = [str(item) for item in contract_errors]

    if task.status == TaskStatus.FAILED and task.error:
        lower_error = task.error.lower()
        if "machine-readable output" in lower_error or "schema validation failed" in lower_error:
            status = "failed"
            valid = False
            if ":" in task.error:
                detail = task.error.split(":", 1)[1].strip()
                if detail:
                    errors = [part.strip() for part in detail.split(";") if part.strip()]
            elif not errors:
                errors = [task.error]

    if status == "not_applicable" and task.status == TaskStatus.COMPLETED and task.output:
        status = "unknown"

    return {
        "status": status,
        "valid": valid,
        "errors": errors,
    }


def _contract_validation_rollup(tasks: list[TaskRecord]) -> dict:
    counts = {
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "unknown": 0,
        "not_applicable": 0,
    }
    failed_tasks: list[dict] = []

    for task in tasks:
        summary = _contract_validation_summary(task)
        status = summary["status"]
        counts[status] = counts.get(status, 0) + 1
        if status == "failed":
            failed_tasks.append(
                {
                    "task_id": task.id,
                    "role": task.role.value,
                    "task_type": task.task_type.value,
                    "errors": summary["errors"],
                }
            )

    validated_total = counts["passed"] + counts["failed"]
    pass_rate = round((counts["passed"] / validated_total) * 100, 2) if validated_total else None

    return {
        "counts": counts,
        "validated_total": validated_total,
        "pass_rate": pass_rate,
        "failed_tasks": failed_tasks,
    }


class AgentRuntime:
    def __init__(self, repo_root: Path, worker_count: int = 3) -> None:
        self.repo_root = repo_root
        self.worker_count = worker_count
        self.task_store = TaskStore()
        self.memory_store = MemoryStore(repo_root)
        self.llm_client = LLMClient(repo_root)
        self.prompt_store = PromptStore(repo_root)
        self.docs_store = DocsStore(repo_root)
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._workers: list[asyncio.Task] = []
        self._started = False
        self._dead_letter: dict[str, list[TaskRecord]] = {}
        self._queued_task_ids: set[str] = set()
        self._maintenance_task: asyncio.Task | None = None
        self._maintenance_enabled = os.getenv("AUTONOMOUS_MAINTENANCE_ENABLED", "true").lower() == "true"
        self._maintenance_interval_sec = max(60, int(os.getenv("AUTONOMOUS_MAINTENANCE_INTERVAL_SEC", "1800")))
        self._prompt_quality_min_improvement = float(os.getenv("PROMPT_QUALITY_MIN_IMPROVEMENT", "2.0"))
        self._prompt_quality_min_score = float(os.getenv("PROMPT_QUALITY_MIN_SCORE", "45"))
        self._prompt_update_cooldown_sec = max(0, int(os.getenv("PROMPT_UPDATE_COOLDOWN_SEC", "1800")))
        self._maintenance_targets = self._load_maintenance_targets()
        self._maintenance_tenants = sorted(load_api_key_map().keys())
        self._last_maintenance_at = ""
        self._last_maintenance_enqueued = 0

    async def start(self) -> None:
        if self._started:
            return
        self.memory_store.init_db()
        self._workers = [
            asyncio.create_task(self._worker_loop(f"worker-{idx+1}"))
            for idx in range(self.worker_count)
        ]
        if self._maintenance_enabled:
            self._maintenance_task = asyncio.create_task(self._autonomous_maintenance_loop())
        self._started = True

    async def stop(self) -> None:
        if self._maintenance_task:
            self._maintenance_task.cancel()
            await asyncio.gather(self._maintenance_task, return_exceptions=True)
            self._maintenance_task = None
        for worker in self._workers:
            worker.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        self._started = False

    async def create_run(self, objective: str, context: dict, tenant_id: str) -> str:
        run_id = str(uuid4())
        task = self.task_store.create_task(
            run_id=run_id,
            tenant_id=tenant_id,
            role=AgentRole.ORCHESTRATOR,
            task_type=TaskType.ORCHESTRATE_GOAL,
            objective=objective,
            payload={"context": context},
            max_retries=1,
        )
        await self.enqueue(task.id)
        return run_id

    async def create_prompt_enhancement(
        self,
        *,
        tenant_id: str,
        title: str,
        seed_prompt: str,
        target_file: str,
        bypass_cooldown: bool = False,
    ) -> tuple[str, str]:
        run_id = str(uuid4())
        task = self.task_store.create_task(
            run_id=run_id,
            tenant_id=tenant_id,
            role=AgentRole.ORCHESTRATOR,
            task_type=TaskType.PROMPT_ENHANCE,
            objective=f"Enhance prompt for {title}",
            payload={
                "title": title,
                "seed_prompt": seed_prompt,
                "target_file": target_file,
                "bypass_cooldown": bypass_cooldown,
            },
            max_retries=1,
        )
        await self.enqueue(task.id)
        return run_id, task.id

    async def enqueue(self, task_id: str) -> None:
        if task_id in self._queued_task_ids:
            return
        self._queued_task_ids.add(task_id)
        await self.queue.put(task_id)

    async def _worker_loop(self, worker_name: str) -> None:
        while True:
            task_id = await self.queue.get()
            try:
                self._queued_task_ids.discard(task_id)
                await self._process_task(task_id, worker_name)
            finally:
                self.queue.task_done()

    async def _process_task(self, task_id: str, worker_name: str) -> None:
        task = self.task_store.get_task(task_id)
        if not task:
            return

        if not self.task_store.dependencies_satisfied(task_id):
            return

        self.task_store.set_status(task_id, TaskStatus.RUNNING)
        task = self.task_store.get_task(task_id)
        if not task:
            return

        try:
            response = execute_specialist(task, self.llm_client)
            output = {
                "worker": worker_name,
                "summary": response.summary,
                "artifacts": response.artifacts,
            }

            if task.task_type == TaskType.PROMPT_ENHANCE:
                output = self._persist_enhanced_prompt(task, output)

            if task.task_type == TaskType.DOCS_UPDATE:
                output = self._persist_docs_update(task, output)

            self.task_store.set_status(task_id, TaskStatus.COMPLETED, output=output)
            await self._persist_task_memory(task, output)
            await self._schedule_graph_tasks(task, output)
            await self._enqueue_ready_tasks(task.run_id, task.tenant_id)
        except Exception as exc:
            latest = self.task_store.get_task(task_id)
            if latest and latest.retry_count < latest.max_retries:
                retry_task = self.task_store.increment_retry(task_id, str(exc))
                await self.enqueue(retry_task.id)
            else:
                failed = self.task_store.set_status(task_id, TaskStatus.FAILED, error=str(exc))
                self._dead_letter.setdefault(task.run_id, []).append(failed)

    async def _persist_task_memory(self, task: TaskRecord, output: dict) -> None:
        key = f"tenant-{task.tenant_id}-run-{task.run_id}-{task.task_type.value}"
        content = (
            f"Role={task.role.value}; Objective={task.objective}; "
            f"Summary={output.get('summary', '')}; Artifacts={output.get('artifacts', {})}"
        )
        self.memory_store.upsert(
            key=key,
            memory_type="run_step",
            tags=f"run,{task.role.value},{task.task_type.value},tenant:{task.tenant_id}",
            content=content,
            source=task.id,
            now=utc_now(),
            tenant_id=task.tenant_id,
        )

    async def _schedule_graph_tasks(self, task: TaskRecord, output: dict) -> None:
        if task.role != AgentRole.ORCHESTRATOR or task.task_type != TaskType.ORCHESTRATE_GOAL:
            return

        context_index = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.MEMORY_STEWARD,
            task_type=TaskType.CONTEXT_INDEX,
            objective=task.objective,
            payload={"previous_output": output, "purpose": "early_context_index"},
            parent_task_id=task.id,
            depends_on=[task.id],
            max_retries=2,
        )

        product = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.PRODUCT_MANAGER,
            task_type=TaskType.PRODUCT_FRAME,
            objective=task.objective,
            payload={"previous_output": output},
            parent_task_id=task.id,
            depends_on=[task.id],
            max_retries=2,
        )

        architecture = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.SYSTEM_ARCHITECT,
            task_type=TaskType.ARCHITECTURE_DESIGN,
            objective=task.objective,
            payload={"depends_on": [product.id]},
            parent_task_id=product.id,
            depends_on=[product.id],
            max_retries=2,
        )

        build = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.WEBAPP_BUILDER,
            task_type=TaskType.BUILD_SLICE,
            objective=task.objective,
            payload={"depends_on": [architecture.id]},
            parent_task_id=architecture.id,
            depends_on=[architecture.id],
            max_retries=3,
        )

        security = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.SECURITY_AUDITOR,
            task_type=TaskType.SECURITY_AUDIT,
            objective=task.objective,
            payload={"depends_on": [build.id]},
            parent_task_id=build.id,
            depends_on=[build.id],
            max_retries=2,
        )

        qa = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.QA_RELIABILITY,
            task_type=TaskType.QA_VERIFY,
            objective=task.objective,
            payload={"depends_on": [build.id, security.id]},
            parent_task_id=security.id,
            depends_on=[build.id, security.id],
            max_retries=2,
        )

        docs = self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.DOCUMENTATION_AGENT,
            task_type=TaskType.DOCS_UPDATE,
            objective=task.objective,
            payload={"depends_on": [architecture.id, build.id, security.id, qa.id]},
            parent_task_id=qa.id,
            depends_on=[architecture.id, build.id, security.id, qa.id],
            max_retries=2,
        )

        self.task_store.create_task(
            run_id=task.run_id,
            tenant_id=task.tenant_id,
            role=AgentRole.MEMORY_STEWARD,
            task_type=TaskType.MEMORY_SNAPSHOT,
            objective=task.objective,
            payload={"depends_on": [security.id, qa.id, context_index.id, docs.id]},
            parent_task_id=docs.id,
            depends_on=[security.id, qa.id, context_index.id, docs.id],
            max_retries=2,
        )

    async def _enqueue_ready_tasks(self, run_id: str, tenant_id: str) -> None:
        tasks = self.task_store.list_tasks(run_id=run_id, tenant_id=tenant_id)
        for task in tasks:
            if task.status != TaskStatus.QUEUED:
                continue
            if not self.task_store.dependencies_satisfied(task.id):
                continue
            await self.enqueue(task.id)

    def get_task(self, task_id: str) -> TaskRecord | None:
        return self.task_store.get_task(task_id)

    def list_tasks(self, run_id: str | None = None, tenant_id: str | None = None) -> list[TaskRecord]:
        return self.task_store.list_tasks(run_id=run_id, tenant_id=tenant_id)

    def list_runs(self, tenant_id: str) -> list[RunView]:
        run_ids = self.task_store.list_runs(tenant_id)
        views: list[RunView] = []

        for run_id in run_ids:
            tasks = self.task_store.list_tasks(run_id=run_id, tenant_id=tenant_id)
            if not tasks:
                continue
            statuses = [task.status for task in tasks]
            if TaskStatus.FAILED in statuses:
                overall = TaskStatus.FAILED
            elif all(status == TaskStatus.COMPLETED for status in statuses):
                overall = TaskStatus.COMPLETED
            elif TaskStatus.RUNNING in statuses:
                overall = TaskStatus.RUNNING
            else:
                overall = TaskStatus.QUEUED

            views.append(
                RunView(
                    run_id=run_id,
                    tenant_id=tenant_id,
                    objective=self.task_store.get_run_objective(run_id),
                    status=overall,
                    created_at=self.task_store.get_run_created_at(run_id),
                    updated_at=tasks[-1].updated_at,
                    completed_tasks=sum(1 for s in statuses if s == TaskStatus.COMPLETED),
                    failed_tasks=sum(1 for s in statuses if s == TaskStatus.FAILED),
                    queued_tasks=sum(1 for s in statuses if s == TaskStatus.QUEUED),
                    running_tasks=sum(1 for s in statuses if s == TaskStatus.RUNNING),
                    dead_letter_tasks=len(self._dead_letter.get(run_id, [])),
                )
            )

        return views

    def get_dead_letter(self, run_id: str, tenant_id: str) -> list[TaskRecord]:
        if not self.task_store.run_belongs_to_tenant(run_id, tenant_id):
            return []
        return [task.model_copy(deep=True) for task in self._dead_letter.get(run_id, [])]

    def run_belongs_to_tenant(self, run_id: str, tenant_id: str) -> bool:
        return self.task_store.run_belongs_to_tenant(run_id, tenant_id)

    def get_run_autonomy_health(self, run_id: str, tenant_id: str) -> dict | None:
        if not self.task_store.run_belongs_to_tenant(run_id, tenant_id):
            return None

        tasks = self.task_store.list_tasks(run_id=run_id, tenant_id=tenant_id)
        if not tasks:
            return None

        status_counts = {
            "queued": sum(1 for task in tasks if task.status == TaskStatus.QUEUED),
            "running": sum(1 for task in tasks if task.status == TaskStatus.RUNNING),
            "completed": sum(1 for task in tasks if task.status == TaskStatus.COMPLETED),
            "failed": sum(1 for task in tasks if task.status == TaskStatus.FAILED),
        }

        pending_agents = sorted(
            {
                task.role.value
                for task in tasks
                if task.status in (TaskStatus.QUEUED, TaskStatus.RUNNING)
            }
        )

        retries = [
            {
                "task_id": task.id,
                "role": task.role.value,
                "task_type": task.task_type.value,
                "retry_count": task.retry_count,
                "max_retries": task.max_retries,
                "last_error": task.error,
            }
            for task in tasks
            if task.retry_count > 0
        ]

        orchestrator_task = next(
            (
                task
                for task in tasks
                if task.role == AgentRole.ORCHESTRATOR and task.task_type == TaskType.ORCHESTRATE_GOAL
            ),
            None,
        )

        security_task = next(
            (task for task in reversed(tasks) if task.task_type == TaskType.SECURITY_AUDIT),
            None,
        )
        docs_task = next(
            (task for task in reversed(tasks) if task.task_type == TaskType.DOCS_UPDATE),
            None,
        )

        dead_letter = self._dead_letter.get(run_id, [])
        contract_rollup = _contract_validation_rollup(tasks)

        return {
            "run_id": run_id,
            "tenant_id": tenant_id,
            "objective": self.task_store.get_run_objective(run_id),
            "created_at": self.task_store.get_run_created_at(run_id),
            "updated_at": tasks[-1].updated_at,
            "orchestrator": {
                "status": orchestrator_task.status.value if orchestrator_task else "unknown",
                "task_id": orchestrator_task.id if orchestrator_task else None,
            },
            "task_counts": status_counts,
            "pending_agents": pending_agents,
            "retry_signals": retries,
            "contract_validation": contract_rollup,
            "dead_letter": {
                "count": len(dead_letter),
                "tasks": [
                    {
                        "task_id": task.id,
                        "role": task.role.value,
                        "task_type": task.task_type.value,
                        "error": task.error,
                    }
                    for task in dead_letter
                ],
            },
            "security": {
                "status": security_task.status.value if security_task else "not_started",
                "recommendation": (
                    security_task.output.get("artifacts", {}).get("security_recommendation")
                    if security_task
                    else None
                ),
                "findings": (
                    security_task.output.get("artifacts", {}).get("findings", [])
                    if security_task
                    else []
                ),
            },
            "documentation": {
                "status": docs_task.status.value if docs_task else "not_started",
                "architecture_doc": (
                    docs_task.output.get("artifacts", {}).get("architecture_doc")
                    if docs_task
                    else None
                ),
                "changes_doc": (
                    docs_task.output.get("artifacts", {}).get("changes_doc")
                    if docs_task
                    else None
                ),
            },
        }

    def get_autonomy_status(self) -> dict:
        return {
            "enabled": self._maintenance_enabled,
            "interval_seconds": self._maintenance_interval_sec,
            "tenants": self._maintenance_tenants,
            "target_prompts": [target[1] for target in self._maintenance_targets],
            "last_maintenance_at": self._last_maintenance_at,
            "last_maintenance_enqueued": self._last_maintenance_enqueued,
            "running": self._maintenance_task is not None,
            "prompt_quality_gate": {
                "min_improvement": self._prompt_quality_min_improvement,
                "min_score": self._prompt_quality_min_score,
                "cooldown_seconds": self._prompt_update_cooldown_sec,
            },
        }

    def _persist_enhanced_prompt(self, task: TaskRecord, output: dict) -> dict:
        artifacts = output.get("artifacts", {})
        content = str(artifacts.get("enhanced_prompt", "")).strip()
        title = str(artifacts.get("title", "enhanced-agent")).strip()
        target_file = str(artifacts.get("target_file", "")).strip()
        bypass_cooldown = bool(task.payload.get("bypass_cooldown", False))
        if content:
            gate = self.prompt_store.save_enhanced_prompt_if_better(
                title=title,
                content=content,
                target_file=target_file,
                min_improvement=self._prompt_quality_min_improvement,
                min_score=self._prompt_quality_min_score,
                cooldown_seconds=0 if bypass_cooldown else self._prompt_update_cooldown_sec,
            )
            artifacts["quality_gate"] = gate
            artifacts["bypass_cooldown"] = bypass_cooldown
            if gate.get("saved"):
                artifacts["saved_prompt_path"] = gate.get("file")
            else:
                artifacts["skipped_prompt_path"] = gate.get("file")
            output["artifacts"] = artifacts
        return output

    def _persist_docs_update(self, task: TaskRecord, output: dict) -> dict:
        artifacts = output.get("artifacts", {})
        architecture_notes = str(artifacts.get("architecture_notes", "No architecture notes provided."))
        change_notes = str(artifacts.get("change_notes", "No change notes provided."))
        saved = self.docs_store.update(
            run_id=task.run_id,
            objective=task.objective,
            architecture_notes=architecture_notes,
            change_notes=change_notes,
        )
        artifacts.update(saved)
        output["artifacts"] = artifacts
        return output

    async def _autonomous_maintenance_loop(self) -> None:
        while True:
            await asyncio.sleep(self._maintenance_interval_sec)
            self._maintenance_targets = self._load_maintenance_targets()
            total = 0
            for tenant_id in self._maintenance_tenants:
                total += await self._enqueue_prompt_maintenance_for_tenant(tenant_id)
            self._last_maintenance_enqueued = total
            self._last_maintenance_at = utc_now()

    async def _enqueue_prompt_maintenance_for_tenant(self, tenant_id: str) -> int:
        count = 0
        for title, target_file in self._maintenance_targets:
            seed_prompt = self._read_prompt_seed(target_file)
            if not seed_prompt:
                continue
            await self.create_prompt_enhancement(
                tenant_id=tenant_id,
                title=f"{title} Maintenance",
                seed_prompt=seed_prompt,
                target_file=target_file,
            )
            count += 1
        return count

    def _read_prompt_seed(self, target_file: str) -> str:
        agent_path = self.repo_root / "agents" / target_file
        if agent_path.exists():
            text = agent_path.read_text(encoding="utf-8")
            return text[:6000]

        legacy_file_name = target_file.replace(".agents.md", ".prompt.md")
        legacy_path = self.repo_root / ".github" / "prompts" / legacy_file_name
        if not legacy_path.exists():
            return ""
        text = legacy_path.read_text(encoding="utf-8")
        return text[:6000]

    def _load_maintenance_targets(self) -> list[tuple[str, str]]:
        agents_dir = self.repo_root / "agents"
        if not agents_dir.exists():
            return []
        targets: list[tuple[str, str]] = []
        for agent_file in sorted(agents_dir.glob("*.agents.md")):
            name = agent_file.name
            title = name.replace(".agents.md", "").replace("-", " ").title()
            targets.append((title, name))

        # Backward compatibility fallback for repositories still on legacy prompt files.
        if not targets:
            prompts_dir = self.repo_root / ".github" / "prompts"
            if prompts_dir.exists():
                for prompt_file in sorted(prompts_dir.glob("*.prompt.md")):
                    name = prompt_file.name.replace(".prompt.md", ".agents.md")
                    title = name.replace(".agents.md", "").replace("-", " ").title()
                    targets.append((title, name))
        return targets
