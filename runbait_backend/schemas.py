"""
Pydantic schemas for all structured Gemini outputs and internal data models.
All AI calls use these schemas to enforce JSON structure.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


# ── Phase 1: Repo Context ────────────────────────────────────────────────────

class RepoContext(BaseModel):
    repo_url: str
    readme: str
    file_tree: List[str]
    package_json: Optional[str] = None
    framework: str
    detected_routes: List[str]
    key_files: dict


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


# ── Phase 4: Playwright Execution ─────────────────────────────────────────────

class StepResult(BaseModel):
    index: int
    action: str
    target: str
    success: bool
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    label: Optional[str] = None


class FlowExecutionResult(BaseModel):
    flow_name: str
    overall_success: bool
    steps_passed: int
    steps_failed: int
    steps: List[StepResult]
    console_errors: List[str]
    duration_seconds: float


# ── Phase 6: Regression Judgment ─────────────────────────────────────────────

class RegressionVerdict(BaseModel):
    flow: str = Field(description="Name of the flow that was tested")
    bug_found: bool = Field(description="True if a regression or bug was detected")
    severity: Optional[str] = Field(default=None, description="high, medium, or low — only set when bug_found is true")
    bug_type: Optional[str] = Field(default=None, description="visual, behavioral, or functional — only set when bug_found is true")
    description: str = Field(description="One-line summary of the finding (or 'No issues found' if clean)")
    evidence_step: Optional[int] = Field(default=None, description="Step index that provides the clearest evidence")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    details: str = Field(description="Detailed multi-sentence analysis of what was observed in the screenshots and logs")


class AnalysisReport(BaseModel):
    verdicts: List[RegressionVerdict]
    overall_status: str = Field(description="One of: passed, failed, warning")
    total_flows_tested: int
    bugs_found: int
    summary: str = Field(description="3-5 sentence executive summary of the entire test run")
