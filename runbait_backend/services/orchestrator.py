import os
import asyncio
from openai import OpenAI
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
CF_TEXT_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"
CF_JUDGE_MODEL = "@cf/meta/llama-3.2-11b-vision-instruct"

def clean_error_message(e: Exception) -> str:
    err_str = str(e)

    # Cloudflare deprecated model (410)
    if "410" in err_str or "deprecated" in err_str.lower():
        model_hint = ""
        m = re.search(r"@cf/[^\s'\"]+", err_str)
        if m:
            model_hint = f" (model: {m.group(0)})"
        return (
            f"Cloudflare AI model has been deprecated{model_hint}. "
            "Please update the model name in the backend config. "
            f"Raw: {err_str[:300]}"
        )
    if "429" in err_str:
        return f"Cloudflare AI Rate Limit Exceeded: Please wait a moment and try again. Raw: {err_str[:200]}"
    if "403" in err_str or "401" in err_str:
        return (
            f"Cloudflare AI Key Invalid or Permission Denied: "
            f"Check CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID on Render. "
            f"Raw: {err_str[:300]}"
        )
    if "400" in err_str:
        return f"Invalid argument passed to Cloudflare AI. Raw: {err_str[:300]}"

    # Try to extract just the message if it's a dict/json
    try:
        match = re.search(r'(\{.*\})', err_str, re.DOTALL)
        if match:
            json_str = match.group(1).replace("'", '"')
            data = json.loads(json_str)
            if "error" in data and "message" in data["error"]:
                return f"Cloudflare AI Error: {data['error']['message']}"
    except Exception:
        pass

    return err_str[:500]


async def run_phases_1_to_3(run_id: str):
    run = get_run(run_id)
    if not run:
        return

    update_run_status(run_id, "phase1-3")
    
    github_token = os.getenv("GITHUB_TOKEN")
    cf_key = os.getenv("CLOUDFLARE_API_TOKEN")
    cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")

    if not cf_key or not cf_account:
        update_run_status(run_id, "failed", error="CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID not set on backend")
        return

    try:
        cf_client = OpenAI(
            api_key=cf_key,
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1",
        )
        owner, repo_name = run["repo"].split("/")[-2:] # simple extraction
        
        # Run Phase 1, 2, 3 sequentially
        ctx = extract_repo_context(owner, repo_name, github_token)
        flow_file = discover_flows(ctx, client=cf_client, model_name=CF_TEXT_MODEL)
        impact_result, pr_data = analyze_pr_impact(
            owner, repo_name, run["pr_number"], flow_file,
            client=cf_client,
            token=github_token,
            model_name=CF_TEXT_MODEL,
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
    
    cf_key = os.getenv("CLOUDFLARE_API_TOKEN")
    cf_account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    try:
        cf_client = OpenAI(
            api_key=cf_key,
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1",
        )
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
                client=cf_client,
                model_name=CF_JUDGE_MODEL,
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
