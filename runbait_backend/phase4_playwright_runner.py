"""
Phase 4 — Playwright Flow Runner

Executes the selected user flows against a running application.
Takes screenshots at every checkpoint step and on any step failure.

Designed to run headlessly inside GitHub Actions.
The app must already be running at app_url before this phase starts.

Output structure per run:
    output/
      screenshots/
        {flow_name}/
          step_01_{label}.png
          step_02_{label}.png
      execution_logs/
        {flow_name}.json
"""

import json
import time
from pathlib import Path
from typing import Optional

from playwright.sync_api import sync_playwright, Page, BrowserContext, Error as PlaywrightError

from schemas import FlowFile, UserFlow, FlowStep, StepResult, FlowExecutionResult


# Timeout (ms) for each step action
STEP_TIMEOUT_MS = 10_000

# Timeout (ms) for page navigation
NAV_TIMEOUT_MS = 20_000


# ── Step Execution Helpers ────────────────────────────────────────────────────

def _smart_click(page: Page, target: str) -> None:
    """
    Try multiple Playwright locator strategies to click an element.
    Strategies are tried in order from most semantic to most fragile.
    """
    strategies = [
        lambda: page.get_by_role("button", name=target).first.click(timeout=STEP_TIMEOUT_MS),
        lambda: page.get_by_role("link", name=target).first.click(timeout=STEP_TIMEOUT_MS),
        lambda: page.get_by_text(target, exact=False).first.click(timeout=STEP_TIMEOUT_MS),
        lambda: page.locator(target).first.click(timeout=STEP_TIMEOUT_MS),
    ]

    last_error = None
    for strategy in strategies:
        try:
            strategy()
            return
        except Exception as e:
            last_error = e
            continue

    raise Exception(f"Could not click '{target}': {last_error}")


def _smart_fill(page: Page, target: str, value: str) -> None:
    """Try multiple strategies to fill an input field."""
    strategies = [
        lambda: page.get_by_label(target, exact=False).first.fill(value, timeout=STEP_TIMEOUT_MS),
        lambda: page.get_by_placeholder(target, exact=False).first.fill(value, timeout=STEP_TIMEOUT_MS),
        lambda: page.locator(target).first.fill(value, timeout=STEP_TIMEOUT_MS),
    ]

    last_error = None
    for strategy in strategies:
        try:
            strategy()
            return
        except Exception as e:
            last_error = e
            continue

    raise Exception(f"Could not fill '{target}': {last_error}")


def _screenshot_path(output_dir: Path, flow_name: str, index: int, label: str) -> Path:
    """Build a deterministic screenshot path."""
    safe_label = label.replace(" ", "_").replace("/", "-")[:40]
    folder = output_dir / "screenshots" / flow_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"step_{index:02d}_{safe_label}.png"


def _execute_step(
    page: Page,
    step: FlowStep,
    step_index: int,
    base_url: str,
    output_dir: Path,
    flow_name: str,
) -> StepResult:
    """Execute a single flow step. Always returns a StepResult (never raises)."""
    label = step.label or f"{step.action}_{step.target[:20]}"
    screenshot_path: Optional[str] = None

    try:
        if step.action == "navigate":
            url = step.target if step.target.startswith("http") else base_url.rstrip("/") + step.target
            page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)

        elif step.action == "click":
            _smart_click(page, step.target)

        elif step.action == "fill":
            _smart_fill(page, step.target, step.value or "")

        elif step.action == "scroll":
            page.evaluate("window.scrollBy(0, 400)")

        elif step.action == "wait":
            page.wait_for_timeout(2000)

        elif step.action == "screenshot":
            pass  # screenshot taken below

        # Take screenshot if this is a checkpoint OR explicit screenshot step
        if step.checkpoint or step.action == "screenshot":
            path = _screenshot_path(output_dir, flow_name, step_index, label)
            page.screenshot(path=str(path), full_page=False)
            screenshot_path = str(path)

        return StepResult(
            index=step_index,
            action=step.action,
            target=step.target,
            success=True,
            screenshot_path=screenshot_path,
            label=label,
        )

    except Exception as exc:
        # Always take a failure screenshot so the judge has evidence
        try:
            path = _screenshot_path(output_dir, flow_name, step_index, f"FAILED_{label}")
            page.screenshot(path=str(path), full_page=False)
            screenshot_path = str(path)
        except Exception:
            pass

        return StepResult(
            index=step_index,
            action=step.action,
            target=step.target,
            success=False,
            error=str(exc),
            screenshot_path=screenshot_path,
            label=label,
        )


# ── Flow Runner ───────────────────────────────────────────────────────────────

def _run_single_flow(
    flow: UserFlow,
    base_url: str,
    output_dir: Path,
    context: BrowserContext,
) -> FlowExecutionResult:
    """Run one flow in a fresh page and return the execution result."""
    page = context.new_page()
    console_errors: list[str] = []

    # Capture console errors
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    step_results: list[StepResult] = []
    start = time.time()

    for i, step in enumerate(flow.steps, 1):
        result = _execute_step(page, step, i, base_url, output_dir, flow.name)
        step_results.append(result)

        # If a navigate or critical step failed, continue anyway — capture what we can

    page.close()

    passed = sum(1 for s in step_results if s.success)
    failed = len(step_results) - passed

    return FlowExecutionResult(
        flow_name=flow.name,
        overall_success=failed == 0,
        steps_passed=passed,
        steps_failed=failed,
        steps=step_results,
        console_errors=console_errors[:20],  # cap to 20
        duration_seconds=round(time.time() - start, 2),
    )


def run_flows(
    selected_flow_names: list[str],
    flow_file: FlowFile,
    app_url: str,
    output_dir: Path,
) -> list[FlowExecutionResult]:
    """
    Main entry point for Phase 4.

    Launches a single Chromium instance, runs each selected flow in a fresh
    browser page (same context — cookies/state are shared), captures screenshots,
    and saves per-flow execution logs.

    Returns a list of FlowExecutionResult objects.
    """
    # Resolve flows to run
    flows_to_run = [f for f in flow_file.flows if f.name in selected_flow_names]

    if not flows_to_run:
        return []

    logs_dir = output_dir / "execution_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    results: list[FlowExecutionResult] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],  # required in GitHub Actions
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            ignore_https_errors=True,
        )

        for flow in flows_to_run:
            result = _run_single_flow(flow, app_url, output_dir, context)
            results.append(result)

            # Save execution log
            log_path = logs_dir / f"{flow.name}.json"
            with open(log_path, "w") as f:
                json.dump(result.model_dump(), f, indent=2)

        context.close()
        browser.close()

    return results
