import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel

from core.security import get_current_user
from services.run_service import create_run, get_run
from services.orchestrator import run_phases_1_to_3, run_phase_6

router = APIRouter(prefix="/api/runs", tags=["runs"])

class RunRequest(BaseModel):
    repo: str
    pr_number: int
    is_demo: bool = False
    start_command: Optional[str] = None
    install_command: Optional[str] = None

class WebhookPayload(BaseModel):
    status: str
    execution_results: list = []
    error: Optional[str] = None
    artifact_id: Optional[str] = None

@router.post("")
async def start_run(req: RunRequest, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    run_id = create_run(
        user_id=user["id"],
        repo=req.repo,
        pr_number=req.pr_number,
        is_demo=req.is_demo,
        start_command=req.start_command,
        install_command=req.install_command
    )
    
    background_tasks.add_task(run_phases_1_to_3, run_id)
    return {"run_id": run_id, "status": "pending"}

@router.get("/{run_id}")
async def get_run_status(run_id: str, user: dict = Depends(get_current_user)):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run["user_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return run

@router.get("/{run_id}/runner-data")
async def get_runner_data(run_id: str):
    # Endpoint for GitHub Action to fetch flow data
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    return {
        "flows": run["results"].get("flows", {}),
        "selected_flow_names": [sf["flow"] for sf in run["results"].get("impact_result", {}).get("selected_flows", [])]
    }

@router.post("/{run_id}/webhook")
async def github_actions_webhook(run_id: str, payload: WebhookPayload, background_tasks: BackgroundTasks):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
        
    if payload.status == "success":
        # Note: We can fetch artifacts using artifact_id here if needed, or phase_6 handles it.
        # But for now, just trigger phase 6
        background_tasks.add_task(run_phase_6, run_id, payload.execution_results)
    else:
        from services.run_service import update_run_status
        update_run_status(run_id, "failed", error=payload.error or "GitHub Actions execution failed.")
        
    return {"status": "accepted"}
