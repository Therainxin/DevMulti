"""Typed data contracts shared by DevOrbit agents, CLI, and reports."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Severity(str, Enum):
    """Severity level assigned to a review finding."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """High-level category for a code issue."""

    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    TESTING = "testing"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


class ReviewMode(str, Enum):
    """Supported review target modes."""

    DIRECTORY = "directory"
    DIFF = "diff"


class ProviderName(str, Enum):
    """Known LLM provider names."""

    MOCK = "mock"
    OPENAI_COMPATIBLE = "openai-compatible"
    MIMO_COMPATIBLE = "mimo-compatible"


class FileSummary(BaseModel):
    """Summary of one scanned source or text file."""

    path: str
    language: str
    line_count: int = Field(ge=0)
    size_bytes: int = Field(ge=0)
    sha1: str | None = None
    is_test: bool = False
    is_dependency_file: bool = False
    is_entrypoint: bool = False
    notes: list[str] = Field(default_factory=list)


class RepositorySnapshot(BaseModel):
    """Snapshot of repository structure available to review agents."""

    root: str
    mode: ReviewMode = ReviewMode.DIRECTORY
    files: list[FileSummary] = Field(default_factory=list)
    file_tree: list[str] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    frameworks: list[str] = Field(default_factory=list)
    dependency_files: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    test_directories: list[str] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)
    target_paths: list[str] = Field(default_factory=list)
    ignored_directories: list[str] = Field(default_factory=list)
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def file_count(self) -> int:
        """Return the number of scanned files."""

        return len(self.files)

    @property
    def total_lines(self) -> int:
        """Return the total number of scanned lines."""

        return sum(file.line_count for file in self.files)


class CodeIssue(BaseModel):
    """A code review finding produced by an agent."""

    title: str
    description: str
    severity: Severity = Severity.MEDIUM
    category: IssueCategory = IssueCategory.MAINTAINABILITY
    file_path: str | None = None
    line: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    evidence: str | None = None
    recommendation: str | None = None
    agent: str = "reviewer"


class FixSuggestion(BaseModel):
    """A concrete repair suggestion linked to a code issue."""

    issue_title: str
    summary: str
    patch_hint: str
    affected_files: list[str] = Field(default_factory=list)
    risk_level: Severity = Severity.MEDIUM
    confidence: float = Field(ge=0.0, le=1.0, default=0.75)
    requires_human_review: bool = True


class TestPlan(BaseModel):
    """Validation plan generated for the current review run."""

    summary: str
    commands: list[str] = Field(default_factory=list)
    available_commands: list[str] = Field(default_factory=list)
    focus_areas: list[str] = Field(default_factory=list)
    regression_tests: list[str] = Field(default_factory=list)
    missing_tests: list[str] = Field(default_factory=list)
    rationale: str


class AgentStep(BaseModel):
    """Trace entry for one action performed by an agent."""

    agent_name: str
    role: str
    action: str
    input_summary: str
    output_summary: str
    observation: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["ok", "warning", "error"] = "ok"


class ShowcaseBrief(BaseModel):
    """Human-readable application or demo material."""

    headline: str
    summary: str
    demo_metrics: dict[str, str] = Field(default_factory=dict)
    honesty_note: str


class ArchitectureSummary(BaseModel):
    """Readable architecture understanding generated from a repository snapshot."""

    summary: str
    entry_files: list[str] = Field(default_factory=list)
    core_modules: list[str] = Field(default_factory=list)
    test_directories: list[str] = Field(default_factory=list)
    risk_areas: list[str] = Field(default_factory=list)
    llm_observation: str


class AgentRunReport(BaseModel):
    """Complete output of one DevOrbit multi-agent run."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    project_name: str
    provider: ProviderName
    mode: ReviewMode
    repository_snapshot: RepositorySnapshot
    architecture_summary: ArchitectureSummary | None = None
    discovered_issues: list[CodeIssue] = Field(default_factory=list)
    fix_suggestions: list[FixSuggestion] = Field(default_factory=list)
    test_plan: TestPlan
    agent_steps: list[AgentStep] = Field(default_factory=list)
    showcase: ShowcaseBrief
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    demo: bool = True

    @property
    def repository(self) -> RepositorySnapshot:
        """Compatibility alias for the repository snapshot."""

        return self.repository_snapshot

    @property
    def issues(self) -> list[CodeIssue]:
        """Compatibility alias for discovered issues."""

        return self.discovered_issues

    @property
    def fixes(self) -> list[FixSuggestion]:
        """Compatibility alias for fix suggestions."""

        return self.fix_suggestions

    @property
    def tests(self) -> TestPlan:
        """Compatibility alias for the generated test plan."""

        return self.test_plan

    @property
    def traces(self) -> list[AgentStep]:
        """Compatibility alias for agent trace steps."""

        return self.agent_steps

    def write_markdown(self, output_path: Path) -> Path:
        """Write this report as Markdown and return the output path."""

        from devorbit.report import render_markdown

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_markdown(self), encoding="utf-8")
        return output_path


ReviewReport = AgentRunReport
RepositoryFile = FileSummary
AgentTrace = AgentStep
