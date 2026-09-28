import json
import re
from openai import OpenAI
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
- IMPORTANT: Output ONLY valid, complete JSON. Do not truncate the JSON output.
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

Respond ONLY with valid JSON matching the FlowFile schema. Keep each flow to 3-5 steps maximum to ensure the response fits within token limits.
"""


def _extract_json(content: str) -> str:
    """
    Attempt to extract a valid JSON string from the LLM response.
    Handles markdown code fences and truncated JSON.
    """
    # Strip markdown fences
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # If the JSON is complete, return as-is
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass

    # Try to extract the outermost JSON object using brace matching
    match = re.search(r"\{", content)
    if match:
        start = match.start()
        depth = 0
        last_valid_end = None
        in_string = False
        escape_next = False
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
                    last_valid_end = i + 1
                    break

        if last_valid_end:
            candidate = content[start:last_valid_end]
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

    # Last resort: return the raw content and let the caller surface the error
    return content


def discover_flows(ctx: RepoContext, client: OpenAI, model_name: str = "@cf/meta/llama-3.1-8b-instruct-fast") -> FlowFile:
    """
    Main entry point for Phase 2.
    Calls Cloudflare AI with the repo context and returns a validated FlowFile.
    """
    prompt = _build_prompt(ctx)

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
    )

    raw = response.choices[0].message.content or ""
    finish_reason = response.choices[0].finish_reason

    if finish_reason == "length":
        # Model hit the token limit — output is likely truncated
        raise RuntimeError(
            f"Cloudflare AI response was cut off (finish_reason='length'). "
            f"The model ran out of tokens. Raw output (first 500 chars): {raw[:500]}"
        )

    content = _extract_json(raw)

    try:
        return FlowFile.model_validate_json(content)
    except Exception as parse_err:
        raise ValueError(
            f"Phase 2 JSON parse failed.\n"
            f"finish_reason={finish_reason}\n"
            f"Raw content (first 800 chars):\n{raw[:800]}\n\n"
            f"Original error: {parse_err}"
        ) from parse_err

