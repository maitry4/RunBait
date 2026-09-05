import os
import requests
import json
import base64
from pathlib import Path
from phase4_playwright_runner import run_flows
from schemas import FlowFile

def main():
    run_id = os.environ.get("RUN_ID")
    callback_url = os.environ.get("CALLBACK_URL")
    
    if not run_id or not callback_url:
        print("Missing RUN_ID or CALLBACK_URL")
        return

    # To avoid needing auth in the GitHub Action runner just to get the flows,
    # the backend should pass a temporary token or we can fetch a specific open endpoint.
    # We will fetch from GET /api/runs/{run_id}/public (we need to add this endpoint)
    # Alternatively, passing the flows as an input string or artifact to the workflow is better.
    # Let's assume we add an endpoint `GET /api/runs/{run_id}/runner-data`
    
    # We need the backend URL which we can derive from callback_url
    # e.g. callback_url: https://api.runbait.com/api/runs/123/webhook
    backend_url = callback_url.rsplit("/api/runs", 1)[0]
    
    print(f"Fetching run data for {run_id} from {backend_url}...")
    resp = requests.get(f"{backend_url}/api/runs/{run_id}/runner-data")
    if resp.status_code != 200:
        print(f"Failed to fetch run data: {resp.text}")
        requests.post(callback_url, json={"status": "failed", "error": "Failed to fetch run data"})
        return
        
    run_data = resp.json()
    flows_dict = run_data["flows"]
    selected_flow_names = run_data["selected_flow_names"]
    
    flow_file = FlowFile.model_validate(flows_dict)
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    print("Running Playwright tests...")
    execution_results = run_flows(
        selected_flow_names=selected_flow_names,
        flow_file=flow_file,
        app_url="http://localhost:3000", # TODO: dynamic port if needed
        output_dir=output_dir
    )
    
    # Send results back
    payload = {
        "status": "success",
        "execution_results": [r.model_dump() for r in execution_results]
    }
    
    print(f"Sending webhook to {callback_url}...")
    post_resp = requests.post(callback_url, json=payload)
    print(f"Webhook response: {post_resp.status_code}")
    
if __name__ == "__main__":
    main()
