"""
Phase 6 — Regression Judge (AI Step 3)

For each executed flow, sends:
  - The flow definition (what was supposed to happen)
  - The execution log (what actually happened, step by step)
  - All checkpoint screenshots (inline multimodal images)
  - The PR diff context (why this flow was selected)

Gemini (gemini-3.1-flash-lite) returns a detailed RegressionVerdict.

The final AnalysisReport aggregates all verdicts and writes report.json.
"""

import json
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from schemas import (
    UserFlow, FlowFile, FlowExecutionResult,
    RegressionVerdict, AnalysisReport,
)


SYSTEM_PROMPT = """You are a senior QA engineer performing regression analysis on a web application.
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
"""


def _load_screenshot_parts(steps: list, max_images: int = 10) -> list:
    """
    Load checkpoint and failure screenshots as Gemini image parts.
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
            label = step.label or f"step {step.index}"
            status = "✓ passed" if step.success else "✗ FAILED"
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/png"))
            parts.append(types.Part.from_text(
                text=f"[Screenshot — Step {step.index}: {step.action} '{step.target}' — {status}]"
            ))
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

Based on all of the above, provide a detailed RegressionVerdict.
"""


def judge_flow(
    flow: UserFlow,
    result: FlowExecutionResult,
    pr_context: str,
    client: genai.Client,
    model_name: str,
) -> RegressionVerdict:
    """
    Run Gemini multimodal judgment for a single flow.
    Returns a RegressionVerdict with detailed analysis.
    """
    text_prompt = _build_judge_prompt(flow, result, pr_context)
    screenshot_parts = _load_screenshot_parts(result.steps)

    # Build content: screenshots first, then the text analysis request
    contents = screenshot_parts + [types.Part.from_text(text=text_prompt)]

    response = client.models.generate_content(
        model=model_name,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=RegressionVerdict,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    if response.parsed:
        return response.parsed

    return RegressionVerdict(**json.loads(response.text))


def build_report(
    verdicts: list[RegressionVerdict],
    output_dir: Path,
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

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "report.json"
    with open(report_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)

    return report
