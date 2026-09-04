"""
Pydantic schemas for structured Gemini outputs.
All AI calls use these schemas to enforce JSON structure.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Phase 1: Repo Context (not an AI schema, just a typed dict) ──────────────

class RepoContext(BaseModel):
    repo_url: str
    readme: str
    file_tree: List[str]          # relative paths, filtered to relevant files
    package_json: Optional[str]   # raw content if found
    framework: str                # e.g. "Next.js", "React+Vite", "Unknown"
    detected_routes: List[str]    # URL paths inferred from file structure
    key_files: dict               # filename -> content snippet for route/page files


# ── Phase 2: Flow Discovery ───────────────────────────────────────────────────

class FlowStep(BaseModel):
    action: str = Field(description="One of: navigate, click, fill, scroll, screenshot, wait")
    target: str = Field(description="URL path, element text, CSS selector, or label")
    value: Optional[str] = Field(default=None, description="Value to fill for 'fill' actions")
    checkpoint: bool = Field(default=False, description="If true, take a screenshot at this step")
    label: Optional[str] = Field(default=None, description="Human-readable label for this step")


class UserFlow(BaseModel):
    name: str = Field(description="Short identifier, e.g. 'homepage', 'project-filter', 'search'")
    description: str = Field(description="One sentence: what user journey this tests")
    entry_url: str = Field(description="Starting URL path, e.g. '/' or '/projects'")
    steps: List[FlowStep]


class FlowFile(BaseModel):
    flows: List[UserFlow]


# ── Phase 3: PR Impact Analysis ───────────────────────────────────────────────

class SelectedFlow(BaseModel):
    flow: str = Field(description="Name of the flow (must match a name from FlowFile)")
    reason: str = Field(description="One sentence explaining why this flow is affected by the PR")
    priority: str = Field(description="One of: high, medium, low")


class PRImpactResult(BaseModel):
    selected_flows: List[SelectedFlow]
    summary: str = Field(description="2-3 sentence summary of what the PR changes and which areas are at risk")
