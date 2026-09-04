"""
Phase 2 — Flow Discovery (AI Step 1)

Takes the structured RepoContext from Phase 1 and asks Gemini to generate
a FlowFile: a list of testable user journeys for the application.

Uses the new google-genai SDK with native Pydantic structured output.
"""

import json
from google import genai
from google.genai import types
from schemas import RepoContext, FlowFile


SYSTEM_PROMPT = """You are a senior QA engineer analyzing a web application repository.
Your task is to identify testable user journeys (flows) from the repository context provided.

Rules:
- Focus on what a REAL USER would do in a browser
- Only include flows that are realistic for this specific application
- Each flow should be self-contained and testable end-to-end
- Steps should use simple, reliable locator strategies (visible text, roles)
- Mark important state-change moments as checkpoints (screenshot = true)
- Aim for 3-7 flows maximum — quality over quantity
- Steps should reflect what the app ACTUALLY does based on the repo context
"""


def _build_prompt(ctx: RepoContext) -> str:
    """Build the prompt text from the repo context."""

    tree_summary = "\n".join(ctx.file_tree[:100])
    if len(ctx.file_tree) > 100:
        tree_summary += f"\n... and {len(ctx.file_tree) - 100} more files"

    key_files_summary = ""
    for filename, content in ctx.key_files.items():
        key_files_summary += f"\n--- {filename} ---\n{content[:1000]}\n"

    routes_summary = "\n".join(ctx.detected_routes) if ctx.detected_routes else "(none detected)"

    return f"""Analyze this web application repository and generate testable user flows.

## Repository Info
URL: {ctx.repo_url}
Framework: {ctx.framework}

## README
{ctx.readme}

## File Tree (filtered)
{tree_summary}

## Detected URL Routes
{routes_summary}

## Key File Contents
{key_files_summary}

Based on the above, generate a FlowFile with realistic user journeys for this application.
Each flow must have:
- A short name (snake_case)
- A clear description
- An entry URL (must be a real route from this app)
- Steps with specific actions

Respond ONLY with valid JSON matching the FlowFile schema.
"""


def discover_flows(ctx: RepoContext, client: genai.Client, model_name: str = "gemini-2.5-flash") -> FlowFile:
    """
    Main entry point for Phase 2.
    Calls Gemini with the repo context and returns a validated FlowFile.
    The new google-genai SDK handles Pydantic schemas natively via response.parsed.
    """
    prompt = _build_prompt(ctx)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=FlowFile,
        ),
    )

    # response.parsed returns a validated Pydantic instance directly
    if response.parsed:
        return response.parsed

    # Fallback: parse from text
    return FlowFile(**json.loads(response.text))
