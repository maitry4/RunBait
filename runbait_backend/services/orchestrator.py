import os
import asyncio
from google import genai
import requests
import json
import re

from phase1_repo_context import extract_repo_context
from phase2_flow_discovery import discover_flows
from phase3_pr_impact import analyze_pr_impact
from phase6_regression_judge import judge_flow, build_report

from services.run_service import get_run, update_run_status
from core.config import get_settings

settings = get_settings()
GEMINI_MODEL = "gemini-2.5-flash"
JUDGE_MODEL = "gemini-3.1-flash-lite"

def clean_error_message(e: Exception) -> str:
    err_str = str(e)
    if "429" in err_str and "RESOURCE_EXHAUSTED" in err_str:
        return "Gemini API Rate Limit Exceeded: Please wait a moment and try again (Free tier limits apply)."
    if "403" in err_str and ("PERMISSION_DENIED" in err_str or "API_KEY_INVALID" in err_str):
        return "Gemini API Key Invalid or Permission Denied: Please check your API key."
    if "400" in err_str and "INVALID_ARGUMENT" in err_str:
        return "Invalid argument passed to Gemini API. Please check your input."
    
    # Try to extract just the message if it's a dict/json
    try:
        match = re.search(r'(\{.*\})', err_str, re.DOTALL)
        if match:
            json_str = match.group(1).replace("'", '"')
            data = json.loads(json_str)
            if "error" in data and "message" in data["error"]:
                return f"Gemini API Error: {data['error']['message']}"
    except Exception:
        pass
        
    return err_str

async def run_phases_1_to_3(run_id: str):
    run = get_run(run_id)
    if not run:
        return

    update_run_status(run_id, "phase1-3")
    
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        update_run_status(run_id, "failed", error="GEMINI_API_KEY not set on backend")
        return

    try:
        gemini_client = genai.Client(api_key=gemini_key)
        owner, repo_name = run["repo"].split("/")[-2:] # simple extraction
        
        # Run Phase 1, 2, 3 sequentially
        ctx = extract_repo_context(owner, repo_name, github_token)
        flow_file = discover_flows(ctx, client=gemini_client, model_name=GEMINI_MODEL)
        impact_result, pr_data = analyze_pr_impact(
            owner, repo_name, run["pr_number"], flow_file,
            client=gemini_client,
            token=github_token,
            model_name=GEMINI_MODEL,
        )

        update_run_status(run_id, "github-actions", results_update={
            "flows": flow_file.model_dump(),
            "impact_result": {
                "summary": impact_result.summary,
                "selected_flows": [sf.model_dump() for sf in impact_result.selected_flows]
            },
            "pr_data": pr_data
        })

        if not impact_result.selected_flows:
            update_run_status(run_id, "completed", results_update={"message": "No flows selected."})
            return

        # Trigger GitHub Action
        trigger_github_action(run_id, owner, repo_name, run)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        update_run_status(run_id, "failed", error=clean_error_message(e))

def trigger_github_action(run_id: str, owner: str, repo_name: str, run: dict):
    # Triggers `.github/workflows/runbait_worker.yml` in our own repository.
    # We assume the RunBait repo owner and name are available or we can hardcode for this project.
    # Wait, what's our repo? We can define it in settings or assume a default.
    # Let's use a dummy or read from env.
    runbait_owner = os.getenv("RUNBAIT_REPO_OWNER", "maitry4")
    runbait_repo = os.getenv("RUNBAIT_REPO_NAME", "RunBait")
    github_token = os.getenv("GITHUB_TOKEN") # Needs repo scope to trigger workflow
    
    url = f"https://api.github.com/repos/{runbait_owner}/{runbait_repo}/actions/workflows/runbait_worker.yml/dispatches"
    
    callback_url = f"{settings.BACKEND_URL}/api/runs/{run_id}/webhook"

    inputs = {
        "target_repo": f"{owner}/{repo_name}",
        "pr_number": str(run["pr_number"]),
        "run_id": run_id,
        "callback_url": callback_url,
    }
    
    if run.get("install_command"):
        inputs["install_command"] = run["install_command"]
    if run.get("start_command"):
        inputs["start_command"] = run["start_command"]

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    payload = {
        "ref": "main",
        "inputs": inputs
    }
    
    print(f"Triggering GitHub Action at {url} with payload {payload}")
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code not in (200, 204):
        print(f"Failed to trigger action: {resp.text}")
        update_run_status(run_id, "failed", error=f"Failed to trigger workflow: {resp.text}")


async def run_phase_6(run_id: str, execution_results: list):
    run = get_run(run_id)
    if not run:
        return
        
    update_run_status(run_id, "phase6")
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    try:
        gemini_client = genai.Client(api_key=gemini_key)
        from schemas import FlowExecutionResult, FlowFile, PRImpactResult
        
        # reconstruct needed objects
        flows_dict = run["results"].get("flows", {})
        flow_file = FlowFile.model_validate(flows_dict)
        
        pr_data = run["results"].get("pr_data", {})
        impact_summary = run["results"].get("impact_result", {}).get("summary", "")
        pr_number = run["pr_number"]
        
        pr_context_str = f"PR #{pr_number}: {pr_data.get('title', '')}\n{impact_summary}"
        
        verdicts = []
        for exec_res_dict in execution_results:
            exec_result = FlowExecutionResult.model_validate(exec_res_dict)
            flow_def = next((f for f in flow_file.flows if f.name == exec_result.flow_name), None)
            if not flow_def:
                continue
                
            verdict = judge_flow(
                flow=flow_def,
                result=exec_result,
                pr_context=pr_context_str,
                client=gemini_client,
                model_name=JUDGE_MODEL,
            )
            verdicts.append(verdict)
            
        report = build_report(verdicts, output_dir=None) # avoid writing to disk
        
        update_run_status(run_id, "completed", results_update={
            "report": {
                "overall_status": report.overall_status,
                "summary": report.summary,
                "verdicts": [v.model_dump() for v in report.verdicts]
            },
            "execution_results": execution_results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        update_run_status(run_id, "failed", error=clean_error_message(e))
