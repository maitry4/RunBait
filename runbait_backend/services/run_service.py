import uuid
from typing import Dict, Any, Optional

RUNS: Dict[str, dict] = {}

def create_run(user_id: str, repo: str, pr_number: int, is_demo: bool, start_command: Optional[str] = None, install_command: Optional[str] = None) -> str:
    run_id = str(uuid.uuid4())
    RUNS[run_id] = {
        "id": run_id,
        "user_id": user_id,
        "repo": repo,
        "pr_number": pr_number,
        "status": "pending",  # pending, phase1-3, github-actions, phase6, completed, failed
        "is_demo": is_demo,
        "start_command": start_command,
        "install_command": install_command,
        "results": {},
        "error": None,
    }
    return run_id

def get_run(run_id: str) -> Optional[dict]:
    return RUNS.get(run_id)

def update_run_status(run_id: str, status: str, results_update: dict = None, error: str = None):
    if run_id in RUNS:
        RUNS[run_id]["status"] = status
        if results_update:
            RUNS[run_id]["results"].update(results_update)
        if error:
            RUNS[run_id]["error"] = error
