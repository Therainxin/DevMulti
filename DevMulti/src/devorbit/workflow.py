"""DevOrbit multi-agent workflow orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from devorbit.agents.workflow_agents import (
    ArchitectureReasonerAgent,
    FixPlannerAgent,
    IssueDiagnosisAgent,
    RepoScannerAgent,
    ReportWriterAgent,
    TestPlannerAgent,
    build_run_report,
)
from devorbit.context import AgentContext
from devorbit.llm.provider import LLMProvider
from devorbit.models import AgentRunReport, AgentStep, ProviderName, ReviewMode
from devorbit.providers.factory import create_provider


class DevOrbitWorkflow:
    """Run DevOrbit agents in sequence and preserve errors in the final report."""

    def __init__(
        self,
        *,
        provider: LLMProvider | None = None,
        provider_name: ProviderName = ProviderName.MOCK,
        output_path: Path = Path("artifacts/devorbit_report.md"),
    ) -> None:
        """Create a workflow with a provider and report output path."""

        self.provider_name = provider_name
        self.provider = provider or create_provider(provider_name)
        self.output_path = output_path
        self.agents = [
            RepoScannerAgent(self.provider),
            ArchitectureReasonerAgent(self.provider),
            IssueDiagnosisAgent(self.provider),
            FixPlannerAgent(self.provider),
            TestPlannerAgent(self.provider),
            ReportWriterAgent(self.provider),
        ]

    def run(self, *, repo_path: Path, target_paths: Iterable[Path] | None = None) -> AgentRunReport:
        """Execute the workflow and return the final structured report."""

        context = AgentContext(
            repo_path=repo_path,
            target_paths=list(target_paths or [repo_path]),
        )

        for agent in self.agents:
            try:
                context = agent.run(context)
            except Exception as exc:  # noqa: BLE001 - workflow must preserve agent failures in reports.
                context.raw_notes.append(f"{agent.name} 执行失败：{exc}")
                context.agent_steps.append(
                    AgentStep(
                        agent_name=agent.name,
                        role=agent.role,
                        action="Agent 执行失败",
                        input_summary=f"正在运行 {agent.name}",
                        output_summary=str(exc),
                        observation=f"{type(exc).__name__}: {exc}",
                        status="error",
                    )
                )
                if isinstance(agent, RepoScannerAgent):
                    break

        report = build_run_report(context, provider_name=self.provider_name)
        if not any(step.agent_name == "report_writer" and step.status == "ok" for step in context.agent_steps):
            try:
                report.write_markdown(self.output_path)
            except Exception as exc:  # noqa: BLE001 - final fallback should not hide earlier context.
                context.agent_steps.append(
                    AgentStep(
                        agent_name="workflow",
                        role="工作流兜底处理",
                        action="报告写入失败",
                        input_summary=str(self.output_path),
                        output_summary=str(exc),
                        observation=f"{type(exc).__name__}: {exc}",
                        status="error",
                    )
                )
                report = build_run_report(context, provider_name=self.provider_name)
        return report


def run_review(
    *,
    path: Path,
    mode: ReviewMode = ReviewMode.DIRECTORY,
    provider_name: ProviderName = ProviderName.MOCK,
) -> AgentRunReport:
    """Compatibility entrypoint for CLI review commands."""

    workflow = DevOrbitWorkflow(provider_name=provider_name)
    report = workflow.run(repo_path=path, target_paths=[path])
    report.repository_snapshot.mode = mode
    return report
