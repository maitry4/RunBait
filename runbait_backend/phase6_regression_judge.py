"""
Phase 6 — Regression Judge (AI Step 3)

For each executed flow, sends:
  - The flow definition (what was supposed to happen)
  - The execution log (what actually happened, step by step)
  - All checkpoint screenshots (inline multimodal images)
  - The PR diff context (why this flow was selected)

Returns a detailed RegressionVerdict. The final AnalysisReport
aggregates all verdicts and writes report.json.
"""

import json
import re
import base64
from pathlib import Path
from typing import Optional

from openai import OpenAI

from schemas import (
    UserFlow, FlowFile, FlowExecutionResult,
    RegressionVerdict, AnalysisReport,
)


_VERDICT_EXAMPLE = """{
  "flow": "flow_name",
  "bug_found": true,
  "severity": "high",
  "bug_type": "visual",
  "description": "One-line summary of the finding",
  "evidence_step": 2,
  "confidence": 0.9,
  "details": "Detailed multi-sentence analysis of what was observed."
}"""

SYSTEM_PROMPT = f"""You are a senior QA engineer performing regression analysis on a web application.
You will receive:
1. The user flow definition — what steps were intended
2. The execution log — what actually happened (pass/fail per step)
3. Screenshots taken at key checkpoints and on failures
4. Context about what this PR changed

Your job is to determine whether a regression occurred.

Analysis guidelines:
- A regression is something that BROKE relative to expected behavior
- Step failures are always bugs unless the step target was ambiguous
- Visual screenshots: look for broken layouts, missing elements, error messages, or wrong content
- Be specific and detailed in your 'details' field — reference exact step numbers and screenshot observations
- confidence: 0.9+ means you are very sure, 0.5-0.9 means likely, below 0.5 means uncertain
- If the flow ran perfectly with no issues, say so clearly with bug_found=false
- severity and bug_type are REQUIRED when bug_found is true; omit them when bug_found is false
- bug_type must be one of: visual | behavioral | functional

Respond ONLY with JSON in this exact shape — no markdown, no extra fields:
{_VERDICT_EXAMPLE}
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


def _load_screenshot_parts(steps: list, max_images: int = 10) -> list:
    """
    Load checkpoint and failure screenshots as base64 encoded strings for OpenAI format.
    Skips missing files silently.
    """
    parts = []
    loaded = 0

    for step in steps:
        if loaded >= max_images:
            break
        if not step.screenshot_path:
            continue
        path = Path(step.screenshot_path)
        if not path.exists():
            continue

        try:
            with open(path, "rb") as f:
                image_bytes = f.read()
            b64_image = base64.b64encode(image_bytes).decode('utf-8')
            status = "✓ passed" if step.success else "✗ FAILED"
            parts.append({
                "type": "text",
                "text": f"[Screenshot — Step {step.index}: {step.action} '{step.target}' — {status}]"
            })
            parts.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{b64_image}"
                }
            })
            loaded += 1
        except Exception:
            continue

    return parts


def _build_judge_prompt(
    flow: UserFlow,
    result: FlowExecutionResult,
    pr_context: str,
) -> str:
    """Build the text portion of the multimodal judgment prompt."""

    # Summarize steps compactly
    steps_summary = []
    for step in result.steps:
        status = "PASS" if step.success else "FAIL"
        error_str = f" | Error: {step.error}" if step.error else ""
        steps_summary.append(
            f"  [{status}] Step {step.index}: {step.action} '{step.target}'{error_str}"
        )

    return f"""Analyze the following browser test execution for regressions.

## PR Context
{pr_context}

## Flow Under Test
Name: {flow.name}
Description: {flow.description}
Entry URL: {flow.entry_url}

## Expected Steps
{chr(10).join(f"  {i+1}. {s.action} '{s.target}'" + (f" = '{s.value}'" if s.value else "") for i, s in enumerate(flow.steps))}

## Execution Results
Overall: {"PASSED" if result.overall_success else "FAILED"}
Steps passed: {result.steps_passed} / {result.steps_passed + result.steps_failed}
Duration: {result.duration_seconds}s

Step-by-step:
{chr(10).join(steps_summary)}

Console errors logged: {len(result.console_errors)}
{chr(10).join(f"  - {e}" for e in result.console_errors[:5]) if result.console_errors else "  (none)"}

## Screenshots
The screenshots above were taken at checkpoint steps and on failures.
Use them as primary evidence for visual and behavioral regressions.

Output ONLY the JSON verdict now.
"""


def judge_flow(
    flow: UserFlow,
    result: FlowExecutionResult,
    pr_context: str,
    client: OpenAI,
    model_name: str,
) -> RegressionVerdict:
    """
    Run Cloudflare multimodal judgment for a single flow.
    Returns a RegressionVerdict with detailed analysis.
    """
    text_prompt = _build_judge_prompt(flow, result, pr_context)
    screenshot_parts = _load_screenshot_parts(result.steps)

    # Build content: text first, then screenshots
    content = [{"type": "text", "text": text_prompt}] + screenshot_parts

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=1536,
    )

    raw = response.choices[0].message.content or ""
    finish_reason = response.choices[0].finish_reason

    if finish_reason == "length":
        raise RuntimeError(
            f"Phase 6 Cloudflare AI response was cut off (finish_reason='length') "
            f"for flow '{flow.name}'. Raw output (first 500 chars): {raw[:500]}"
        )

    extracted = _extract_json(raw)

    try:
        data = json.loads(extracted)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Phase 6 JSON decode failed for flow '{flow.name}'.\n"
            f"finish_reason={finish_reason}\nRaw (first 800 chars):\n{raw[:800]}\nError: {e}"
        ) from e

    try:
        return RegressionVerdict.model_validate(data)
    except Exception as parse_err:
        raise ValueError(
            f"Phase 6 schema validation failed for flow '{flow.name}'.\n"
            f"Data: {json.dumps(data, indent=2)[:800]}\nError: {parse_err}"
        ) from parse_err




def build_report(
    verdicts: list[RegressionVerdict],
    output_dir: Optional[Path] = None,
) -> AnalysisReport:
    """
    Aggregate all per-flow verdicts into a final AnalysisReport
    and write report.json to the output directory.
    """
    bugs_found = sum(1 for v in verdicts if v.bug_found)
    high_severity = any(v.severity == "high" for v in verdicts if v.bug_found)

    if bugs_found == 0:
        overall_status = "passed"
    elif high_severity:
        overall_status = "failed"
    else:
        overall_status = "warning"

    # Build summary text
    if bugs_found == 0:
        summary = (
            f"All {len(verdicts)} flow(s) passed with no regressions detected. "
            "The changes in this PR appear safe from a user-journey perspective."
        )
    else:
        flow_names = ", ".join(v.flow for v in verdicts if v.bug_found)
        summary = (
            f"{bugs_found} regression(s) detected across {len(verdicts)} flow(s) tested. "
            f"Affected flows: {flow_names}. "
            f"Overall status: {overall_status.upper()}. "
            "Review the detailed verdicts below for evidence and remediation guidance."
        )

    report = AnalysisReport(
        verdicts=verdicts,
        overall_status=overall_status,
        total_flows_tested=len(verdicts),
        bugs_found=bugs_found,
        summary=summary,
    )

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "report.json"
        with open(report_path, "w") as f:
            json.dump(report.model_dump(), f, indent=2)

    return report
