"""
RunBait Agent — Main CLI Entry Point

Usage:
    python runbait_agent.py

Requires environment variables (or .env file):
    GITHUB_TOKEN   — GitHub personal access token (read-only scope is fine)
    GEMINI_API_KEY — Google AI API key

What it does:
    1. Fetches all open PRs from the target repository
    2. Lets you select a PR interactively
    3. Extracts repo context (Phase 1) — no cloning, pure GitHub API
    4. Asks Gemini to discover all user flows (Phase 2)
    5. Asks Gemini to select which flows the PR affects (Phase 3)
    6. Prints a summary and saves flows.json + selected_flows.json
"""

import os
import sys
import json
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
from rich.text import Text

from phase1_repo_context import extract_repo_context
from phase2_flow_discovery import discover_flows
from phase3_pr_impact import analyze_pr_impact

# ── Config ────────────────────────────────────────────────────────────────────

# Target repository (hardcoded for v1 simulation)
OWNER = "maitry4"
REPO = "opensource.razorpay.com"

# Output directory for generated files
OUTPUT_DIR = Path(__file__).parent / "output"

# Gemini model to use
GEMINI_MODEL = "gemini-2.5-flash"

console = Console()


# ── GitHub Helpers ────────────────────────────────────────────────────────────

def fetch_pull_requests(owner: str, repo: str, token: Optional[str], state: str = "all") -> list[dict]:
    """Fetch PRs from GitHub API (open + closed, newest first)."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        headers=headers,
        params={"state": state, "per_page": 30, "sort": "updated", "direction": "desc"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ── Display Helpers ────────────────────────────────────────────────────────────

def display_pr_table(prs: list[dict]) -> None:
    """Render a rich table of pull requests."""
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
            str(i),
            f"#{pr['number']}",
            pr.get("title", ""),
            pr.get("user", {}).get("login", ""),
            state_str,
            updated,
        )

    console.print()
    console.print(table)


def display_flows(flow_file) -> None:
    """Render discovered flows."""
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
            console.print(f"     [dim]{j:02}.[/dim] [cyan]{step.action}[/cyan] [white]{step.target}[/white]{value_str}{checkpoint}")


def display_selected_flows(impact_result, flow_file) -> None:
    """Render selected flows from PR impact analysis."""
    console.print()
    console.print(Panel.fit(
        "[bold magenta]✦ PR Impact Analysis[/bold magenta]",
        border_style="magenta",
    ))
    console.print(f"\n  [dim]{impact_result.summary}[/dim]")

    if not impact_result.selected_flows:
        console.print("\n  [yellow]No flows selected — PR may not affect user-facing behavior.[/yellow]")
        return

    console.print(f"\n  [bold]Flows to run:[/bold] {len(impact_result.selected_flows)}\n")
    
    priority_colors = {"high": "red", "medium": "yellow", "low": "dim"}
    
    for sf in impact_result.selected_flows:
        color = priority_colors.get(sf.priority, "white")
        # Find the matching flow for step count
        matching = next((f for f in flow_file.flows if f.name == sf.flow), None)
        steps_count = f"({len(matching.steps)} steps)" if matching else ""
        
        console.print(f"  [{color}]● {sf.flow}[/{color}] {steps_count}")
        console.print(f"    [dim]{sf.reason}[/dim]")
        console.print(f"    Priority: [{color}]{sf.priority.upper()}[/{color}]")
        console.print()


def save_outputs(flow_file, impact_result, pr_data) -> None:
    """Save flows.json and selected_flows.json to the output directory."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    pr_num = pr_data.get("number", "unknown")
    
    # flows.json
    flows_path = OUTPUT_DIR / "flows.json"
    with open(flows_path, "w") as f:
        json.dump(flow_file.model_dump(), f, indent=2)
    
    # selected_flows.json
    selected_path = OUTPUT_DIR / f"pr_{pr_num}_selected_flows.json"
    with open(selected_path, "w") as f:
        json.dump({
            "pr_number": pr_num,
            "pr_title": pr_data.get("title", ""),
            "summary": impact_result.summary,
            "selected_flows": [sf.model_dump() for sf in impact_result.selected_flows],
            "full_flows": flow_file.model_dump(),
        }, f, indent=2)
    
    console.print(f"\n  [dim]Saved:[/dim] [cyan]{flows_path}[/cyan]")
    console.print(f"  [dim]Saved:[/dim] [cyan]{selected_path}[/cyan]")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    load_dotenv()

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not gemini_key:
        console.print("[red]Error:[/red] GEMINI_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    # Create a single shared client for all Gemini calls
    gemini_client = genai.Client(api_key=gemini_key)

    console.print()
    console.print(Panel(
        "[bold white]RunBait[/bold white] [dim]— AI-powered PR regression testing[/dim]",
        border_style="bright_blue",
        padding=(0, 2),
    ))

    # ── Step 1: Fetch PRs ─────────────────────────────────────────────────────
    console.print(f"\n[dim]Fetching pull requests from[/dim] [cyan]{OWNER}/{REPO}[/cyan]...")
    
    try:
        prs = fetch_pull_requests(OWNER, REPO, github_token)
    except requests.HTTPError as e:
        console.print(f"[red]GitHub API error:[/red] {e}")
        if e.response.status_code == 401:
            console.print("[dim]Tip: Set GITHUB_TOKEN in your .env for private repos or higher rate limits.[/dim]")
        sys.exit(1)

    if not prs:
        console.print("[yellow]No pull requests found.[/yellow]")
        sys.exit(0)

    display_pr_table(prs)

    # ── Step 2: Select a PR ───────────────────────────────────────────────────
    console.print()
    selection = IntPrompt.ask(
        f"  [bold]Select a PR[/bold] (1–{len(prs)})",
        default=1,
    )
    if selection < 1 or selection > len(prs):
        console.print("[red]Invalid selection.[/red]")
        sys.exit(1)

    selected_pr_meta = prs[selection - 1]
    pr_number = selected_pr_meta["number"]
    
    console.print(f"\n  Selected: [bold cyan]#{pr_number}[/bold cyan] — {selected_pr_meta['title']}")
    console.print()

    # Confirm run
    go = Prompt.ask("  Run analysis?", choices=["y", "n"], default="y")
    if go != "y":
        console.print("[dim]Aborted.[/dim]")
        sys.exit(0)

    # ── Phase 1: Repo Context ─────────────────────────────────────────────────
    console.print()
    with Live(Spinner("dots", text=" [cyan]Phase 1[/cyan] — Extracting repo context via GitHub API..."), refresh_per_second=10):
        ctx = extract_repo_context(OWNER, REPO, github_token)

    console.print(f"  [green]✓[/green] Phase 1 complete — Framework: [bold]{ctx.framework}[/bold], "
                  f"Files: [bold]{len(ctx.file_tree)}[/bold], "
                  f"Routes detected: [bold]{len(ctx.detected_routes)}[/bold]")

    # ── Phase 2: Flow Discovery ───────────────────────────────────────────────
    console.print()
    with Live(Spinner("dots", text=" [cyan]Phase 2[/cyan] — Asking Gemini to discover user flows..."), refresh_per_second=10):
        flow_file = discover_flows(ctx, client=gemini_client, model_name=GEMINI_MODEL)

    console.print(f"  [green]✓[/green] Phase 2 complete — [bold]{len(flow_file.flows)}[/bold] flows discovered")
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

    console.print(f"  [green]✓[/green] Phase 3 complete — [bold]{len(impact_result.selected_flows)}[/bold] flows selected for testing")
    display_selected_flows(impact_result, flow_file)

    # ── Save outputs ──────────────────────────────────────────────────────────
    console.print()
    console.print(Panel.fit("[bold green]✦ Analysis Complete[/bold green]", border_style="green"))
    save_outputs(flow_file, impact_result, pr_data)

    console.print()
    console.print("  [dim]Next step: run the selected Playwright flows against the live app.[/dim]")
    console.print()


if __name__ == "__main__":
    main()
