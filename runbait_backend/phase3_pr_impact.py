"""
Phase 3 — PR Impact Analysis (AI Step 2)

Takes:
- The FlowFile from Phase 2 (all discovered flows)
- The PR diff (list of changed files + patch text)
- Basic PR metadata (title, description)

Deterministically maps changed files → candidate flows, then asks Gemini to
rank and select which flows should actually be run.
"""

import json
import re
import requests
from typing import Optional
from google import genai
from google.genai import types
from schemas import FlowFile, PRImpactResult


SYSTEM_PROMPT = """You are a senior QA engineer doing PR impact analysis.
Given a list of user flows and a PR diff, determine which flows are most likely
to be affected by the changes in this PR.

Rules:
- Only select flows that have a real connection to the changed code
- Explain your reasoning clearly and specifically (reference actual filenames)
- Prioritize flows as: high (likely broken), medium (possibly affected), low (tangentially related)
- If a PR only changes styles/docs, select flows that test the visual appearance
- If no flows are affected, return an empty selected_flows list
"""


def _fetch_pr_diff(owner: str, repo: str, pr_number: int, token: Optional[str]) -> tuple[dict, list[dict]]:
    """Fetch PR metadata and changed files from GitHub API."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    base = f"https://api.github.com/repos/{owner}/{repo}"

    pr_resp = requests.get(f"{base}/pulls/{pr_number}", headers=headers, timeout=30)
    pr_resp.raise_for_status()
    pr_data = pr_resp.json()

    files_resp = requests.get(
        f"{base}/pulls/{pr_number}/files",
        headers=headers,
        params={"per_page": 100},
        timeout=30,
    )
    files_resp.raise_for_status()

    return pr_data, files_resp.json()


def _prefilter_flows(flow_file: FlowFile, changed_file_paths: list[str]) -> list[str]:
    """
    Deterministic pre-filter: keyword-match changed filenames against flow names/descriptions.
    Returns candidate flow names to narrow the AI prompt.
    """
    candidates = set()

    for flow in flow_file.flows:
        flow_keywords = set(
            re.sub(r"[-_]", " ", flow.name).lower().split()
            + re.sub(r"[^a-z ]", " ", flow.description.lower()).split()
        )

        for filepath in changed_file_paths:
            filename = (
                filepath.lower()
                .replace("-", " ").replace("_", " ")
                .replace("/", " ").replace(".", " ")
            )
            if flow_keywords & set(filename.split()):
                candidates.add(flow.name)
                break

    # If no keyword match, expose all flows so AI can decide
    if not candidates:
        candidates = {f.name for f in flow_file.flows}

    return list(candidates)


def _build_prompt(flow_file: FlowFile, pr_data: dict, changed_files: list[dict], candidate_flow_names: list[str]) -> str:
    """Build the AI prompt for PR impact analysis."""
    files_summary = []
    for f in changed_files:
        patch = f.get("patch", "")[:500]
        files_summary.append(
            f"  {f['status'].upper()}: {f['filename']}\n"
            f"  +{f.get('additions', 0)} / -{f.get('deletions', 0)} lines\n"
            + (f"  Patch:\n{patch}\n" if patch else "")
        )

    candidate_flows = [f for f in flow_file.flows if f.name in candidate_flow_names]
    flows_text = json.dumps(
        [{"name": f.name, "description": f.description, "entry_url": f.entry_url} for f in candidate_flows],
        indent=2,
    )

    return f"""Analyze this PR and select which user flows need to be tested.

## PR Information
Title: {pr_data.get('title', 'N/A')}
Description: {pr_data.get('body', 'N/A') or '(no description)'}
Files changed: {len(changed_files)}

## Changed Files
{"".join(files_summary)}

## Available User Flows (pre-filtered candidates)
{flows_text}

Select which flows are affected by this PR. Respond ONLY with valid JSON matching the PRImpactResult schema.
"""


def analyze_pr_impact(
    owner: str,
    repo: str,
    pr_number: int,
    flow_file: FlowFile,
    client: genai.Client,
    token: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
) -> tuple[PRImpactResult, dict]:
    """
    Main entry point for Phase 3.
    Returns (PRImpactResult, pr_metadata).
    """
    pr_data, changed_files = _fetch_pr_diff(owner, repo, pr_number, token)

    changed_paths = [f["filename"] for f in changed_files]
    candidates = _prefilter_flows(flow_file, changed_paths)

    prompt = _build_prompt(flow_file, pr_data, changed_files, candidates)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=PRImpactResult,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    if response.parsed:
        return response.parsed, pr_data

    return PRImpactResult(**json.loads(response.text)), pr_data
