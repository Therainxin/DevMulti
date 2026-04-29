"""Reviewer agent."""

from __future__ import annotations

from devorbit.agents.base import BaseAgent
from devorbit.context import AgentContext
from devorbit.models import CodeIssue, IssueCategory, Severity


class ReviewerAgent(BaseAgent):
    """Identify deterministic review findings from repository context."""

    name = "reviewer"
    role = "代码质量、风险与可维护性评审"

    def run(self, context: AgentContext) -> AgentContext:
        """Analyze the repository snapshot and populate discovered issues."""

        if context.repository_snapshot is None:
            raise ValueError("ReviewerAgent 需要先生成 context.repository_snapshot。")

        snapshot = context.repository_snapshot
        issues: list[CodeIssue] = []

        if snapshot.file_count == 0:
            issues.append(
                CodeIssue(
                    title="未发现可评审文件",
                    description="目标目录中没有可评审的 UTF-8 文本文件。",
                    severity=Severity.HIGH,
                    category=IssueCategory.TESTING,
                    recommendation="确认评审路径，或先添加源码文件再运行 Agent 工作流。",
                    agent=self.name,
                )
            )

        for file in snapshot.files:
            if file.line_count > 400:
                issues.append(
                    CodeIssue(
                        title="文件过大，可能混杂多个职责",
                        description="该文件行数偏多，会增加评审和回归测试难度。",
                        severity=Severity.MEDIUM,
                        category=IssueCategory.MAINTAINABILITY,
                        file_path=file.path,
                        evidence=f"单文件包含 {file.line_count} 行。",
                        recommendation="拆分独立职责，或为关键分支补充聚焦测试。",
                        agent=self.name,
                    )
                )
            if file.language == "Python" and file.path.endswith("__init__.py") and file.line_count > 80:
                issues.append(
                    CodeIssue(
                        title="包初始化文件包含过多逻辑",
                        description="过重的包初始化逻辑可能带来导入副作用。",
                        severity=Severity.MEDIUM,
                        category=IssueCategory.ARCHITECTURE,
                        file_path=file.path,
                        recommendation="将运行时逻辑移动到明确的模块或函数中。",
                        agent=self.name,
                    )
                )

        if not issues:
            issues.append(
                CodeIssue(
                    title="离线启发式检查未发现阻塞问题",
                    description=(
                        "Mock 评审未检测到结构性阻塞问题。"
                        "后续可接入真实 Provider 做更深入的语义分析。"
                    ),
                    severity=Severity.LOW,
                    category=IssueCategory.MAINTAINABILITY,
                    recommendation="继续运行常规测试，并考虑启用真实 Provider 进行语义评审。",
                    agent=self.name,
                )
            )

        context.discovered_issues = issues
        self.log_step(
            context,
            action="评审代码",
            prompt=f"评审 {snapshot.file_count} 个文件，并按开发影响排序 {len(issues)} 个发现。",
        )
        return context
