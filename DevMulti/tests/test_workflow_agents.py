from pathlib import Path

from devorbit.agents.workflow_agents import (
    ArchitectureReasonerAgent,
    FixPlannerAgent,
    IssueDiagnosisAgent,
    RepoScannerAgent,
    ReportWriterAgent,
    TestPlannerAgent,
)
from devorbit.context import AgentContext
from devorbit.llm.mock import MockLLMProvider
from devorbit.models import IssueCategory, Severity
from devorbit.workflow import DevOrbitWorkflow


FIXTURE_REPO = Path("tests/fixtures/sample_repo")


def _context() -> AgentContext:
    return AgentContext(repo_path=FIXTURE_REPO, target_paths=[FIXTURE_REPO])


def test_repo_scanner_collects_tree_languages_and_dependency_files() -> None:
    context = RepoScannerAgent(MockLLMProvider()).run(_context())
    snapshot = context.repository_snapshot

    assert snapshot is not None
    assert snapshot.file_count >= 4
    assert snapshot.languages["Python"] == 2
    assert "pyproject.toml" in snapshot.dependency_files
    assert "app.py" in snapshot.entrypoints


def test_repo_scanner_detects_frameworks_from_pyproject() -> None:
    context = RepoScannerAgent(MockLLMProvider()).run(_context())

    assert context.repository_snapshot is not None
    assert "FastAPI" in context.repository_snapshot.frameworks
    assert "pytest" in context.repository_snapshot.frameworks


def test_architecture_reasoner_adds_readable_summary() -> None:
    provider = MockLLMProvider()
    context = RepoScannerAgent(provider).run(_context())
    context = ArchitectureReasonerAgent(provider).run(context)

    assert context.architecture_summary is not None
    assert "app.py" in context.architecture_summary.entry_files
    assert context.architecture_summary.core_modules
    assert "架构摘要已生成" in context.architecture_summary.llm_observation


def test_issue_diagnosis_finds_required_issue_types() -> None:
    provider = MockLLMProvider()
    context = RepoScannerAgent(provider).run(_context())
    context = IssueDiagnosisAgent(provider).run(context)
    titles = {issue.title for issue in context.discovered_issues}

    assert "异常捕获范围过宽" in titles
    assert "疑似硬编码密钥或 Token" in titles
    assert "索引访问前缺少边界检查" in titles
    assert "TODO/FIXME 技术债" in titles
    assert "函数过大或复杂度过高" in titles
    assert "缺少测试目录" in titles


def test_issue_diagnosis_attaches_locations_and_categories() -> None:
    provider = MockLLMProvider()
    context = RepoScannerAgent(provider).run(_context())
    context = IssueDiagnosisAgent(provider).run(context)
    secret = next(issue for issue in context.discovered_issues if issue.category == IssueCategory.SECURITY)

    assert secret.file_path == "app.py"
    assert secret.line == 1
    assert secret.severity == Severity.HIGH


def test_fix_planner_creates_suggestions_for_each_issue() -> None:
    provider = MockLLMProvider()
    context = RepoScannerAgent(provider).run(_context())
    context = IssueDiagnosisAgent(provider).run(context)
    context = FixPlannerAgent(provider).run(context)

    assert len(context.fix_suggestions) == len(context.discovered_issues)
    assert any("环境变量" in fix.patch_hint for fix in context.fix_suggestions)
    assert any(fix.risk_level == Severity.HIGH for fix in context.fix_suggestions)


def test_test_planner_suggests_project_commands_and_new_tests() -> None:
    provider = MockLLMProvider()
    context = RepoScannerAgent(provider).run(_context())
    context = IssueDiagnosisAgent(provider).run(context)
    context = FixPlannerAgent(provider).run(context)
    context = TestPlannerAgent(provider).run(context)

    assert context.test_plan is not None
    assert "pytest" in context.test_plan.commands
    assert "ruff check ." in context.test_plan.commands
    assert "mypy ." in context.test_plan.commands
    assert context.test_plan.missing_tests


def test_report_writer_generates_markdown_from_context() -> None:
    provider = MockLLMProvider()
    context = RepoScannerAgent(provider).run(_context())
    context = ArchitectureReasonerAgent(provider).run(context)
    context = IssueDiagnosisAgent(provider).run(context)
    context = FixPlannerAgent(provider).run(context)
    context = TestPlannerAgent(provider).run(context)
    context = ReportWriterAgent(provider).run(context)
    report_path = Path("artifacts/devorbit_report.md")
    content = report_path.read_text(encoding="utf-8")

    assert "项目概览" in content
    assert "app.py" in content
    assert "疑似硬编码密钥或 Token" in content
    assert "pytest" in content


def test_workflow_runs_all_agents_and_writes_report() -> None:
    report = DevOrbitWorkflow().run(repo_path=FIXTURE_REPO)

    assert report.repository_snapshot.file_count >= 4
    assert report.architecture_summary is not None
    assert len(report.agent_steps) == 6
    assert Path("artifacts/devorbit_report.md").exists()


def test_workflow_captures_agent_failure_in_report() -> None:
    report = DevOrbitWorkflow().run(repo_path=Path("tests/fixtures/does_not_exist"))

    assert any(step.status == "error" for step in report.agent_steps)
    assert any(step.agent_name == "repo_scanner" for step in report.agent_steps)
    assert Path("artifacts/devorbit_report.md").exists()
