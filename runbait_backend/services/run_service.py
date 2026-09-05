import uuid
from typing import Dict, Any, Optional
from core.db import supabase

def create_run(user_id: str, repo: str, pr_number: int, is_demo: bool, start_command: Optional[str] = None, install_command: Optional[str] = None) -> str:
    # We let supabase handle ID generation if default gen_random_uuid() is set
    # But it's easier to generate here and return it directly without waiting for a select
    run_id = str(uuid.uuid4())
    data = {
        "id": run_id,
        "user_id": user_id,
        "repo": repo,
        "pr_number": pr_number,
        "status": "pending",
        "is_demo": is_demo,
        "start_command": start_command,
        "install_command": install_command,
        "results": {},
        "error": None
    }
    supabase.table("runs").insert(data).execute()
    return run_id

def get_run(run_id: str) -> Optional[dict]:
    res = supabase.table("runs").select("*").eq("id", run_id).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return None

def update_run_status(run_id: str, status: str, results_update: dict = None, error: str = None):
    # Fetch current results to merge them
    run = get_run(run_id)
    if not run:
        return

    update_data = {"status": status}
    
    if results_update:
        current_results = run.get("results") or {}
        current_results.update(results_update)
        update_data["results"] = current_results
        
    if error:
        update_data["error"] = error
        
    supabase.table("runs").update(update_data).eq("id", run_id).execute()
