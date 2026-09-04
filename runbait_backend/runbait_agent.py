"""
RunBait Agent — Main CLI Entry Point

Usage (interactive, local):
    python runbait_agent.py --app-url http://localhost:3000

Usage (non-interactive, GitHub Actions):
    python runbait_agent.py --app-url http://localhost:3000 --pr 42

Requires environment variables (or .env file):
    GITHUB_TOKEN   — GitHub personal access token (read-only scope is fine)
    GEMINI_API_KEY — Google AI API key

Pipeline:
    Phase 1  Extract repo context via GitHub API (no cloning)
    Phase 2  Gemini discovers all user flows (gemini-2.5-flash)
    Phase 3  Gemini selects flows affected by the PR diff (gemini-2.5-flash)
    Phase 4  Playwright executes selected flows, captures screenshots
    Phase 6  Gemini judges screenshots for regressions (gemini-3.1-flash-lite)
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from google import genai
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box
from rich.spinner import Spinner
from rich.live import Live
from rich.rule import Rule

from phase1_repo_context import extract_repo_context
from phase2_flow_discovery import discover_flows
from phase3_pr_impact import analyze_pr_impact
from phase4_playwright_runner import run_flows
from phase6_regression_judge import judge_flow, build_report

# ── Config ────────────────────────────────────────────────────────────────────

OWNER = "maitry4"
REPO = "opensource.razorpay.com"
OUTPUT_DIR = Path(__file__).parent / "output"

# AI models
GEMINI_MODEL = "gemini-2.5-flash"       # phases 2 & 3 — discovery & selection
JUDGE_MODEL = "gemini-3.1-flash-lite"   # phase 6  — regression judgment

console = Console()


# ── Argument Parsing ──────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RunBait — AI-powered PR regression testing")
    parser.add_argument(
        "--app-url",
        metavar="URL",
        help="Base URL of the running application (e.g. http://localhost:3000). "
             "Required for Playwright execution (phases 4 & 6). "
             "If omitted, only phases 1–3 run (flow discovery + PR analysis).",
    )
    parser.add_argument(
        "--pr",
        metavar="NUMBER",
        type=int,
        help="PR number to analyze. If omitted, shows an interactive selection menu.",
    )
    return parser.parse_args()


# ── GitHub Helpers ────────────────────────────────────────────────────────────

def fetch_pull_requests(owner: str, repo: str, token: Optional[str]) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        params={"state": "all", "per_page": 30, "sort": "updated", "direction": "desc"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── Display Helpers ────────────────────────────────────────────────────────────

def display_pr_table(prs: list[dict]) -> None:
    table = Table(
        title=f"📦  Pull Requests — {OWNER}/{REPO}",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold cyan",
        border_style="bright_black",
    )
    table.add_column("#", style="bold yellow", width=4, justify="right")
    table.add_column("PR", style="dim", width=6, justify="right")
    table.add_column("Title", style="white", min_width=40)
    table.add_column("Author", style="cyan", width=16)
    table.add_column("State", width=8, justify="center")
    table.add_column("Updated", style="dim", width=12)

    for i, pr in enumerate(prs, 1):
        state = pr.get("state", "")
        state_str = "[green]open[/green]" if state == "open" else "[red]closed[/red]"
        updated = pr.get("updated_at", "")[:10]
        table.add_row(
            str(i), f"#{pr['number']}", pr.get("title", ""),
            pr.get("user", {}).get("login", ""), state_str, updated,
        )

    console.print()
    console.print(table)


def display_flows(flow_file) -> None:
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]✦ {len(flow_file.flows)} User Flows Discovered[/bold cyan]",
        border_style="cyan",
    ))
    for i, flow in enumerate(flow_file.flows, 1):
        console.print(f"\n  [bold yellow]{i}. {flow.name}[/bold yellow] — {flow.description}")
        console.print(f"     [dim]Entry: {flow.entry_url}[/dim]")
        for j, step in enumerate(flow.steps, 1):
            checkpoint = " [green]📸[/green]" if step.checkpoint else ""
            value_str = f" → [italic]{step.value}[/italic]" if step.value else ""
            console.print(
                f"     [dim]{j:02}.[/dim] [cyan]{step.action}[/cyan] "
                f"[white]{step.target}[/white]{value_str}{checkpoint}"
            )


def display_selected_flows(impact_result, flow_file) -> None:
    console.print()
    console.print(Panel.fit("[bold magenta]✦ PR Impact Analysis[/bold magenta]", border_style="magenta"))
    console.print(f"\n  [dim]{impact_result.summary}[/dim]")

    if not impact_result.selected_flows:
        console.print("\n  [yellow]No flows selected — PR may not affect user-facing behavior.[/yellow]")
        return

    console.print(f"\n  [bold]Flows to run:[/bold] {len(impact_result.selected_flows)}\n")
    priority_colors = {"high": "red", "medium": "yellow", "low": "dim"}

    for sf in impact_result.selected_flows:
        color = priority_colors.get(sf.priority, "white")
        matching = next((f for f in flow_file.flows if f.name == sf.flow), None)
        steps_count = f"({len(matching.steps)} steps)" if matching else ""
        console.print(f"  [{color}]● {sf.flow}[/{color}] {steps_count}")
        console.print(f"    [dim]{sf.reason}[/dim]")
        console.print(f"    Priority: [{color}]{sf.priority.upper()}[/{color}]")
        console.print()


def display_execution_results(results) -> None:
    console.print()
    console.print(Panel.fit("[bold blue]✦ Playwright Execution[/bold blue]", border_style="blue"))
    console.print()

    for result in results:
        status = "[green]PASSED[/green]" if result.overall_success else "[red]FAILED[/red]"
        console.print(
            f"  [bold]{result.flow_name}[/bold]  {status}  "
            f"[dim]{result.steps_passed}/{result.steps_passed + result.steps_failed} steps · "
            f"{result.duration_seconds}s[/dim]"
        )
        for step in result.steps:
            icon = "[green]✓[/green]" if step.success else "[red]✗[/red]"
            err = f" [dim red]→ {step.error[:80]}[/dim red]" if step.error else ""
            shot = " [green]📸[/green]" if step.screenshot_path else ""
            console.print(
                f"    {icon} [dim]{step.index:02}.[/dim] "
                f"[cyan]{step.action}[/cyan] {step.target}{err}{shot}"
            )
        console.print()


def display_report(report) -> None:
    console.print()
    console.print(Rule())

    status_styles = {
        "passed": ("[bold green]✅ ALL FLOWS PASSED[/bold green]", "green"),
        "failed": ("[bold red]🚨 REGRESSIONS DETECTED[/bold red]", "red"),
        "warning": ("[bold yellow]⚠️  WARNINGS[/bold yellow]", "yellow"),
    }
    title_text, border_color = status_styles.get(
        report.overall_status, ("RunBait Report", "white")
    )

    console.print()
    console.print(Panel.fit(title_text, border_style=border_color))
    console.print(f"\n  [dim]{report.summary}[/dim]\n")

    for verdict in report.verdicts:
        if verdict.bug_found:
            severity_colors = {"high": "red", "medium": "yellow", "low": "cyan"}
            color = severity_colors.get(verdict.severity or "medium", "yellow")
            console.print(f"  [bold {color}]■ {verdict.flow}[/bold {color}]")
            console.print(f"    [{color}]{(verdict.severity or 'unknown').upper()} — {verdict.bug_type or 'unknown'}[/{color}]")
            console.print(f"    [bold white]{verdict.description}[/bold white]")
            console.print(f"    [dim]{verdict.details}[/dim]")
            if verdict.evidence_step:
                console.print(f"    Evidence at step [bold]{verdict.evidence_step}[/bold] · Confidence: {verdict.confidence:.0%}")
        else:
            console.print(f"  [green]■ {verdict.flow}[/green]  [dim]— {verdict.description}[/dim]")
            console.print(f"    [dim]{verdict.details}[/dim]")
        console.print()


def save_phase_outputs(flow_file, impact_result, pr_data) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    pr_num = pr_data.get("number", "unknown")

    flows_path = OUTPUT_DIR / "flows.json"
    with open(flows_path, "w") as f:
        json.dump(flow_file.model_dump(), f, indent=2)

    selected_path = OUTPUT_DIR / f"pr_{pr_num}_selected_flows.json"
    with open(selected_path, "w") as f:
        json.dump({
            "pr_number": pr_num,
            "pr_title": pr_data.get("title", ""),
            "summary": impact_result.summary,
            "selected_flows": [sf.model_dump() for sf in impact_result.selected_flows],
        }, f, indent=2)

    console.print(f"  [dim]Saved:[/dim] [cyan]{flows_path}[/cyan]")
    console.print(f"  [dim]Saved:[/dim] [cyan]{selected_path}[/cyan]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()
    args = parse_args()

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        console.print("[red]Error:[/red] GEMINI_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    gemini_client = genai.Client(api_key=gemini_key)

    console.print()
    console.print(Panel(
        "[bold white]RunBait[/bold white] [dim]— AI-powered PR regression testing[/dim]",
        border_style="bright_blue",
        padding=(0, 2),
    ))

    # ── PR Selection ──────────────────────────────────────────────────────────
    console.print(f"\n[dim]Fetching pull requests from[/dim] [cyan]{OWNER}/{REPO}[/cyan]...")

    try:
        prs = fetch_pull_requests(OWNER, REPO, github_token)
    except requests.HTTPError as e:
        console.print(f"[red]GitHub API error:[/red] {e}")
        sys.exit(1)

    if not prs:
        console.print("[yellow]No pull requests found.[/yellow]")
        sys.exit(0)

    if args.pr:
        # Non-interactive: --pr flag provided (GitHub Actions mode)
        selected_pr_meta = next((p for p in prs if p["number"] == args.pr), None)
        if not selected_pr_meta:
            console.print(f"[red]PR #{args.pr} not found in the last {len(prs)} PRs.[/red]")
            sys.exit(1)
    else:
        # Interactive: show table and prompt
        display_pr_table(prs)
        console.print()
        selection = IntPrompt.ask(f"  [bold]Select a PR[/bold] (1–{len(prs)})", default=1)
        if selection < 1 or selection > len(prs):
            console.print("[red]Invalid selection.[/red]")
            sys.exit(1)
        selected_pr_meta = prs[selection - 1]

        console.print(f"\n  Selected: [bold cyan]#{selected_pr_meta['number']}[/bold cyan] — {selected_pr_meta['title']}")
        go = Prompt.ask("  Run analysis?", choices=["y", "n"], default="y")
        if go != "y":
            console.print("[dim]Aborted.[/dim]")
            sys.exit(0)

    pr_number = selected_pr_meta["number"]
    console.print(f"\n  [dim]Analyzing[/dim] [bold cyan]PR #{pr_number}[/bold cyan]: {selected_pr_meta['title']}")

    # ── Phase 1: Repo Context ─────────────────────────────────────────────────
    console.print()
    with Live(Spinner("dots", text=" [cyan]Phase 1[/cyan] — Extracting repo context..."), refresh_per_second=10):
        ctx = extract_repo_context(OWNER, REPO, github_token)

    console.print(
        f"  [green]✓[/green] Phase 1 — Framework: [bold]{ctx.framework}[/bold], "
        f"Files: [bold]{len(ctx.file_tree)}[/bold], "
        f"Routes: [bold]{len(ctx.detected_routes)}[/bold]"
    )

    # ── Phase 2: Flow Discovery ───────────────────────────────────────────────
    console.print()
    with Live(Spinner("dots", text=" [cyan]Phase 2[/cyan] — Discovering user flows..."), refresh_per_second=10):
        flow_file = discover_flows(ctx, client=gemini_client, model_name=GEMINI_MODEL)

    console.print(f"  [green]✓[/green] Phase 2 — [bold]{len(flow_file.flows)}[/bold] flows discovered")
    display_flows(flow_file)

    # ── Phase 3: PR Impact Analysis ───────────────────────────────────────────
    console.print()
    with Live(Spinner("dots", text=f" [cyan]Phase 3[/cyan] — Analyzing PR #{pr_number} impact..."), refresh_per_second=10):
        impact_result, pr_data = analyze_pr_impact(
            OWNER, REPO, pr_number, flow_file,
            client=gemini_client,
            token=github_token,
            model_name=GEMINI_MODEL,
        )

    console.print(
        f"  [green]✓[/green] Phase 3 — "
        f"[bold]{len(impact_result.selected_flows)}[/bold] flow(s) selected for testing"
    )
    display_selected_flows(impact_result, flow_file)

    # Save phases 1–3 outputs
    console.print()
    save_phase_outputs(flow_file, impact_result, pr_data)

    if not impact_result.selected_flows:
        console.print("\n  [yellow]No flows to execute. Done.[/yellow]\n")
        sys.exit(0)

    if not args.app_url:
        console.print(
            "\n  [dim]Tip: pass [bold]--app-url http://localhost:PORT[/bold] "
            "to run Playwright and get a full regression report.[/dim]\n"
        )
        sys.exit(0)

    # ── Phase 4: Playwright Execution ─────────────────────────────────────────
    selected_names = [sf.flow for sf in impact_result.selected_flows]
    console.print()
    with Live(
        Spinner("dots", text=f" [cyan]Phase 4[/cyan] — Running {len(selected_names)} flow(s) with Playwright..."),
        refresh_per_second=10,
    ):
        execution_results = run_flows(
            selected_flow_names=selected_names,
            flow_file=flow_file,
            app_url=args.app_url,
            output_dir=OUTPUT_DIR,
        )

    console.print(
        f"  [green]✓[/green] Phase 4 — "
        f"[bold]{sum(1 for r in execution_results if r.overall_success)}[/bold]/"
        f"[bold]{len(execution_results)}[/bold] flows passed"
    )
    display_execution_results(execution_results)

    # ── Phase 6: Regression Judgment ──────────────────────────────────────────
    console.print()
    console.print(Panel.fit(
        f"[bold magenta]✦ Phase 6 — AI Regression Analysis ({JUDGE_MODEL})[/bold magenta]",
        border_style="magenta",
    ))

    verdicts = []
    # Build a compact PR context string for the judge
    pr_context_str = (
        f"PR #{pr_number}: {pr_data.get('title', '')}\n"
        f"{impact_result.summary}"
    )

    for exec_result in execution_results:
        # Find the flow definition
        flow_def = next((f for f in flow_file.flows if f.name == exec_result.flow_name), None)
        if not flow_def:
            continue

        with Live(
            Spinner("dots", text=f"   Judging flow: [cyan]{exec_result.flow_name}[/cyan]..."),
            refresh_per_second=10,
        ):
            verdict = judge_flow(
                flow=flow_def,
                result=exec_result,
                pr_context=pr_context_str,
                client=gemini_client,
                model_name=JUDGE_MODEL,
            )
        verdicts.append(verdict)

        status = "[red]BUG FOUND[/red]" if verdict.bug_found else "[green]CLEAN[/green]"
        console.print(f"  [green]✓[/green] [bold]{exec_result.flow_name}[/bold] → {status}")

    # ── Final Report ──────────────────────────────────────────────────────────
    report = build_report(verdicts, OUTPUT_DIR)
    display_report(report)

    report_path = OUTPUT_DIR / "report.json"
    console.print(f"  [dim]Full report saved:[/dim] [cyan]{report_path}[/cyan]")
    console.print()

    # Exit with non-zero code if regressions found (useful for GitHub Actions CI)
    if report.overall_status == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
