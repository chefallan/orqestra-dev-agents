from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from .models import AgentRole, TaskRecord, TaskStatus, TaskType


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TaskStore:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskRecord] = {}
        self._run_meta: Dict[str, Dict[str, str]] = {}
        self._lock = Lock()

    def create_task(
        self,
        *,
        run_id: str,
        tenant_id: str,
        role: AgentRole,
        task_type: TaskType,
        objective: str,
        payload: dict,
        parent_task_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        max_retries: int = 2,
    ) -> TaskRecord:
        now = utc_now()
        task = TaskRecord(
            id=str(uuid4()),
            run_id=run_id,
            tenant_id=tenant_id,
            parent_task_id=parent_task_id,
            depends_on=depends_on or [],
            retry_count=0,
            max_retries=max_retries,
            role=role,
            task_type=task_type,
            objective=objective,
            payload=payload,
            status=TaskStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            self._tasks[task.id] = task
            if run_id not in self._run_meta:
                self._run_meta[run_id] = {
                    "objective": objective,
                    "created_at": now,
                    "tenant_id": tenant_id,
                }
        return task

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            task = self._tasks.get(task_id)
            return task.model_copy(deep=True) if task else None

    def update_task(self, task: TaskRecord) -> None:
        with self._lock:
            self._tasks[task.id] = task

    def set_status(self, task_id: str, status: TaskStatus, *, output: Optional[dict] = None, error: Optional[str] = None) -> TaskRecord:
        with self._lock:
            task = self._tasks[task_id]
            task.status = status
            task.updated_at = utc_now()
            if output is not None:
                task.output = output
            if error is not None:
                task.error = error
            self._tasks[task.id] = task
            return task.model_copy(deep=True)

    def increment_retry(self, task_id: str, error: str) -> TaskRecord:
        with self._lock:
            task = self._tasks[task_id]
            task.retry_count += 1
            task.status = TaskStatus.QUEUED
            task.error = error
            task.updated_at = utc_now()
            self._tasks[task.id] = task
            return task.model_copy(deep=True)

    def list_tasks(self, *, run_id: Optional[str] = None, tenant_id: Optional[str] = None) -> List[TaskRecord]:
        with self._lock:
            tasks: Iterable[TaskRecord] = self._tasks.values()
            if run_id:
                tasks = [task for task in tasks if task.run_id == run_id]
            if tenant_id:
                tasks = [task for task in tasks if task.tenant_id == tenant_id]
            return sorted((task.model_copy(deep=True) for task in tasks), key=lambda t: t.created_at)

    def list_runs(self, tenant_id: str) -> List[str]:
        with self._lock:
            return sorted(
                run_id
                for run_id, meta in self._run_meta.items()
                if meta.get("tenant_id") == tenant_id
            )

    def get_run_objective(self, run_id: str) -> str:
        with self._lock:
            meta = self._run_meta.get(run_id, {})
            return meta.get("objective", "")

    def get_run_created_at(self, run_id: str) -> str:
        with self._lock:
            meta = self._run_meta.get(run_id, {})
            return meta.get("created_at", utc_now())

    def get_run_tenant_id(self, run_id: str) -> str:
        with self._lock:
            meta = self._run_meta.get(run_id, {})
            return meta.get("tenant_id", "")

    def run_belongs_to_tenant(self, run_id: str, tenant_id: str) -> bool:
        with self._lock:
            meta = self._run_meta.get(run_id)
            return bool(meta and meta.get("tenant_id") == tenant_id)

    def dependencies_satisfied(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            return all(
                dep_id in self._tasks and self._tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.depends_on
            )
