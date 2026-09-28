import json
import re
from openai import OpenAI
from schemas import RepoContext, FlowFile


# Exact schema printed in the prompt so the model has no excuse to invent fields.
_SCHEMA_EXAMPLE = """{
  "flows": [
    {
      "name": "example_flow",
      "description": "One sentence describing the user journey",
      "entry_url": "/some-path",
      "steps": [
        {"action": "navigate", "target": "/some-path", "checkpoint": false},
        {"action": "click",    "target": "Button text or CSS selector", "checkpoint": false},
        {"action": "fill",     "target": "Input label or CSS selector", "value": "text to type", "checkpoint": false},
        {"action": "screenshot","target": "full page", "checkpoint": true}
      ]
    }
  ]
}"""

SYSTEM_PROMPT = f"""You are a senior QA engineer generating testable user flows for a web application.

OUTPUT FORMAT — you MUST use exactly these fields for every step, nothing else:
  action     : one of  navigate | click | fill | scroll | screenshot | wait
  target     : URL path (for navigate) OR element text / CSS selector / label (for everything else)
  value      : (optional) text to type — only for "fill" actions
  checkpoint : true | false  — set true only at important state-change moments

Do NOT invent extra fields like "url", "selector", "description", or "screenshot" on steps.

Example output (copy this structure exactly):
{_SCHEMA_EXAMPLE}

Rules:
- Aim for 3-5 flows, each with 3-5 steps (keeps output small and valid)
- Only include flows realistic for THIS specific application
- Respond with ONLY the JSON object — no markdown, no explanation
"""


def _build_prompt(ctx: RepoContext) -> str:
    """Build the prompt text from the repo context."""
    tree_summary = "\n".join(ctx.file_tree[:80])
    if len(ctx.file_tree) > 80:
        tree_summary += f"\n... and {len(ctx.file_tree) - 80} more files"

    key_files_summary = ""
    for filename, content in ctx.key_files.items():
        key_files_summary += f"\n--- {filename} ---\n{content[:800]}\n"

    routes_summary = "\n".join(ctx.detected_routes) if ctx.detected_routes else "(none detected)"

    return f"""Analyze this web application and output a FlowFile JSON (schema shown in system prompt).

## Repository Info
URL: {ctx.repo_url}
Framework: {ctx.framework}

## README (excerpt)
{ctx.readme[:1200]}

## File Tree
{tree_summary}

## Detected URL Routes
{routes_summary}

## Key Files
{key_files_summary}

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

    # Brace-depth matching for truncated output
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


_ACTION_KEYWORDS = {"navigate", "click", "fill", "scroll", "screenshot", "wait"}

def _coerce_steps(data: dict) -> dict:
    """
    Normalise step dicts from the LLM to match FlowStep exactly.
    The model sometimes emits freestyle fields; this maps them to the schema.
    """
    for flow in data.get("flows", []):
        coerced = []
        for step in flow.get("steps", []):
            # ── action ──────────────────────────────────────────────────────
            action = step.get("action", "")
            # If the model wrote a full sentence, infer the action keyword
            if action not in _ACTION_KEYWORDS:
                al = action.lower()
                if "navigate" in al or "go to" in al or "open" in al:
                    action = "navigate"
                elif "click" in al or "press" in al or "tap" in al:
                    action = "click"
                elif "fill" in al or "type" in al or "enter" in al or "input" in al:
                    action = "fill"
                elif "scroll" in al:
                    action = "scroll"
                elif "wait" in al:
                    action = "wait"
                else:
                    action = "screenshot"

            # ── target ──────────────────────────────────────────────────────
            target = (
                step.get("target")
                or step.get("selector")
                or step.get("url")
                or step.get("element")
                or "/"
            )

            # ── checkpoint / screenshot ──────────────────────────────────────
            checkpoint = bool(
                step.get("checkpoint")
                or step.get("screenshot")
            )

            coerced_step = {
                "action": action,
                "target": str(target),
                "checkpoint": checkpoint,
            }
            if step.get("value"):
                coerced_step["value"] = step["value"]
            if step.get("label"):
                coerced_step["label"] = step["label"]

            coerced.append(coerced_step)
        flow["steps"] = coerced
    return data


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
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
    )

    raw = response.choices[0].message.content or ""
    finish_reason = response.choices[0].finish_reason

    if finish_reason == "length":
        raise RuntimeError(
            f"Cloudflare AI response was cut off (finish_reason='length'). "
            f"Raw output (first 500 chars): {raw[:500]}"
        )

    content = _extract_json(raw)

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Phase 2 JSON decode failed.\nfinish_reason={finish_reason}\n"
            f"Raw (first 800 chars):\n{raw[:800]}\nError: {e}"
        ) from e

    data = _coerce_steps(data)

    try:
        return FlowFile.model_validate(data)
    except Exception as parse_err:
        raise ValueError(
            f"Phase 2 schema validation failed after coercion.\n"
            f"Coerced data: {json.dumps(data, indent=2)[:800]}\n"
            f"Error: {parse_err}"
        ) from parse_err
