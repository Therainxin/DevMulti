"""Agent context passed through the DevOrbit workflow."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from devorbit.models import AgentStep, ArchitectureSummary, CodeIssue, FixSuggestion, RepositorySnapshot, TestPlan


class AgentContext(BaseModel):
    """Mutable state shared by cooperating DevOrbit agents."""

    repo_path: Path
    target_paths: list[Path] = Field(default_factory=list)
    repository_snapshot: RepositorySnapshot | None = None
    architecture_summary: ArchitectureSummary | None = None
    discovered_issues: list[CodeIssue] = Field(default_factory=list)
    fix_suggestions: list[FixSuggestion] = Field(default_factory=list)
    test_plan: TestPlan | None = None
    agent_steps: list[AgentStep] = Field(default_factory=list)
    raw_notes: list[str] = Field(default_factory=list)

    def normalized_targets(self) -> list[str]:
        """Return target paths as display strings for prompts and reports."""

        return [str(path) for path in self.target_paths] or [str(self.repo_path)]
