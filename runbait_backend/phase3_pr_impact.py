"""
Phase 3 — PR Impact Analysis (AI Step 2)

Takes:
- The FlowFile from Phase 2 (all discovered flows)
- The PR diff (list of changed files + patch text)
- Basic PR metadata (title, description)

Deterministically maps changed files → candidate flows, then asks the model to
rank and select which flows should actually be run.
"""

import json
import re
import requests
from typing import Optional
from openai import OpenAI
from schemas import FlowFile, PRImpactResult


_SCHEMA_EXAMPLE = """{
  "selected_flows": [
    {
      "flow": "flow_name_from_flow_file",
      "reason": "One sentence: why this flow is affected by the PR",
      "priority": "high"
    }
  ],
  "summary": "2-3 sentence executive summary of what the PR changes and which areas are at risk."
}"""

SYSTEM_PROMPT = f"""You are a senior QA engineer doing PR impact analysis.
Given a list of user flows and a PR diff, determine which flows are most likely
to be affected by the changes in this PR.

Rules:
- Only select flows that have a real connection to the changed code
- Explain your reasoning clearly and specifically (reference actual filenames)
- priority must be exactly one of: high | medium | low
- If no flows are affected, return an empty selected_flows list
- Respond ONLY with JSON in this exact shape — no markdown, no extra fields:

{_SCHEMA_EXAMPLE}
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

Output ONLY the JSON object now.
"""


def _extract_json(content: str) -> str:
    """Strip markdown fences and extract the outermost JSON object."""
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{", content)
    if match:
        start = match.start()
        depth, in_string, escape_next = 0, False, False
        for i, ch in enumerate(content[start:], start=start):
            if escape_next:
                escape_next = False
                continue
            if ch == "\\" and in_string:
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = content[start:i + 1]
                    try:
                        json.loads(candidate)
                        return candidate
                    except json.JSONDecodeError:
                        break
    return content


def analyze_pr_impact(
    owner: str,
    repo: str,
    pr_number: int,
    flow_file: FlowFile,
    client: OpenAI,
    token: Optional[str] = None,
    model_name: str = "@cf/meta/llama-3.1-8b-instruct-fast",
) -> tuple[PRImpactResult, dict]:
    """
    Main entry point for Phase 3.
    Returns (PRImpactResult, pr_metadata).
    """
    pr_data, changed_files = _fetch_pr_diff(owner, repo, pr_number, token)

    changed_paths = [f["filename"] for f in changed_files]
    candidates = _prefilter_flows(flow_file, changed_paths)

    prompt = _build_prompt(flow_file, pr_data, changed_files, candidates)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=1024,
    )

    raw = response.choices[0].message.content or ""
    finish_reason = response.choices[0].finish_reason

    if finish_reason == "length":
        raise RuntimeError(
            f"Phase 3 Cloudflare AI response was cut off (finish_reason='length'). "
            f"Raw output (first 500 chars): {raw[:500]}"
        )

    content = _extract_json(raw)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Phase 3 JSON decode failed.\nfinish_reason={finish_reason}\n"
            f"Raw (first 800 chars):\n{raw[:800]}\nError: {e}"
        ) from e

    try:
        return PRImpactResult.model_validate(data), pr_data
    except Exception as parse_err:
        raise ValueError(
            f"Phase 3 schema validation failed.\n"
            f"Data: {json.dumps(data, indent=2)[:800]}\n"
            f"Error: {parse_err}"
        ) from parse_err
