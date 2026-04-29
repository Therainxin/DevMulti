from pathlib import Path

import pytest
from pydantic import ValidationError

from devorbit.context import AgentContext
from devorbit.models import (
    AgentStep,
    CodeIssue,
    FileSummary,
    IssueCategory,
    RepositorySnapshot,
    Severity,
    TestPlan,
)


def test_repository_snapshot_counts_files_and_lines() -> None:
    snapshot = RepositorySnapshot(
        root="repo",
        files=[
            FileSummary(path="app.py", language="Python", line_count=10, size_bytes=200),
            FileSummary(path="README.md", language="Markdown", line_count=5, size_bytes=80),
        ],
    )

    assert snapshot.file_count == 2
    assert snapshot.total_lines == 15


def test_code_issue_defaults_are_agent_ready() -> None:
    issue = CodeIssue(title="Missing test", description="Critical path has no regression coverage.")

    assert issue.severity == Severity.MEDIUM
    assert issue.category == IssueCategory.MAINTAINABILITY
    assert issue.agent == "reviewer"


def test_file_summary_rejects_negative_counts() -> None:
    with pytest.raises(ValidationError):
        FileSummary(path="broken.py", language="Python", line_count=-1, size_bytes=10)


def test_test_plan_requires_summary_and_rationale() -> None:
    plan = TestPlan(
        summary="Run core checks.",
        commands=["pytest"],
        focus_areas=["testing"],
        regression_tests=["Add a CLI smoke test."],
        rationale="The CLI is the user-facing workflow.",
    )

    assert plan.commands == ["pytest"]
    assert "CLI" in plan.regression_tests[0]


def test_agent_context_defaults_are_isolated() -> None:
    first = AgentContext(repo_path=Path("repo-a"))
    second = AgentContext(repo_path=Path("repo-b"))

    first.discovered_issues.append(CodeIssue(title="A", description="B"))
    first.agent_steps.append(
        AgentStep(
            agent_name="reviewer",
            role="review",
            action="check",
            input_summary="input",
            output_summary="output",
            observation="observation",
        )
    )

    assert len(first.discovered_issues) == 1
    assert second.discovered_issues == []
    assert second.agent_steps == []

