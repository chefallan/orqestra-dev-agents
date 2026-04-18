from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .auth import load_api_key_map, validate_tenant_api_key
from .engine import AgentRuntime, utc_now
from .models import CreateRunRequest, EnhancePromptRequest, MemoryUpsertRequest, TaskRecord, TaskStatus


repo_root = Path(__file__).resolve().parents[2]
runtime = AgentRuntime(repo_root=repo_root)
app = FastAPI(title="Autonomous Agent Runtime", version="0.1.0")
api_keys = load_api_key_map()


def _task_to_api(task: TaskRecord) -> dict:
    payload = task.model_dump()
    payload["contract_validation_summary"] = _contract_validation_summary(task)
    return payload


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
        "errors_count": len(errors),
        "errors": errors,
    }


def require_tenant(
    x_tenant_id: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> str:
    if not x_tenant_id or not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-Tenant-Id or X-Api-Key")
    if not validate_tenant_api_key(x_tenant_id, x_api_key, api_keys):
        raise HTTPException(status_code=403, detail="Invalid tenant credentials")
    return x_tenant_id


@app.on_event("startup")
async def startup_event() -> None:
    await runtime.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await runtime.stop()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "time": utc_now()}


@app.get("/autonomy/status")
def autonomy_status(_: str = Depends(require_tenant)) -> dict:
    return runtime.get_autonomy_status()


@app.post("/runs")
async def create_run(request: CreateRunRequest, tenant_id: str = Depends(require_tenant)) -> dict:
    run_id = await runtime.create_run(request.objective, request.context, tenant_id)
    return {"run_id": run_id, "status": "queued"}


@app.post("/prompts/enhance")
async def enhance_prompt(request: EnhancePromptRequest, tenant_id: str = Depends(require_tenant)) -> dict:
    run_id, task_id = await runtime.create_prompt_enhancement(
        tenant_id=tenant_id,
        title=request.title,
        seed_prompt=request.seed_prompt,
        target_file=request.target_file,
        bypass_cooldown=request.bypass_cooldown,
    )
    return {"run_id": run_id, "task_id": task_id, "status": "queued"}


@app.get("/runs")
def list_runs(tenant_id: str = Depends(require_tenant)) -> list[dict]:
    return [view.model_dump() for view in runtime.list_runs(tenant_id)]


@app.get("/runs/{run_id}/tasks")
def list_run_tasks(run_id: str, tenant_id: str = Depends(require_tenant)) -> list[dict]:
    if not runtime.run_belongs_to_tenant(run_id, tenant_id):
        raise HTTPException(status_code=404, detail="Run not found")
    tasks = runtime.list_tasks(run_id=run_id, tenant_id=tenant_id)
    return [_task_to_api(task) for task in tasks]


@app.get("/runs/{run_id}/autonomy-health")
def get_run_autonomy_health(run_id: str, tenant_id: str = Depends(require_tenant)) -> dict:
    report = runtime.get_run_autonomy_health(run_id, tenant_id)
    if not report:
        raise HTTPException(status_code=404, detail="Run not found")
    return report


@app.get("/tasks/{task_id}")
def get_task(task_id: str, tenant_id: str = Depends(require_tenant)) -> dict:
    task = runtime.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_api(task)


@app.get("/runs/{run_id}/dead-letter")
def get_dead_letter(run_id: str, tenant_id: str = Depends(require_tenant)) -> list[dict]:
    if not runtime.run_belongs_to_tenant(run_id, tenant_id):
        raise HTTPException(status_code=404, detail="Run not found")
    return [_task_to_api(task) for task in runtime.get_dead_letter(run_id, tenant_id)]


@app.get("/memory/search")
def search_memory(
    query: str = Query(min_length=2),
    limit: int = 8,
    tenant_id: str = Depends(require_tenant),
) -> list[dict]:
    return runtime.memory_store.search(query=query, limit=limit, tenant_id=tenant_id)


@app.post("/memory/upsert")
def upsert_memory(request: MemoryUpsertRequest, tenant_id: str = Depends(require_tenant)) -> dict:
    runtime.memory_store.upsert(
        key=f"tenant-{tenant_id}-{request.key}",
        memory_type=request.memory_type,
        tags=request.tags,
        content=request.content,
        source=request.source,
        now=utc_now(),
        tenant_id=tenant_id,
    )
    return {"status": "ok", "key": request.key}
