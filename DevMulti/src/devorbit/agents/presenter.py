"""Presenter agent."""

from __future__ import annotations

from devorbit.agents.base import BaseAgent
from devorbit.context import AgentContext
from devorbit.models import ShowcaseBrief


class PresenterAgent(BaseAgent):
    """Create readable demo and application material."""

    name = "presenter"
    role = "演示叙事与申请材料生成"

    def run(self, context: AgentContext) -> ShowcaseBrief:
        """Create a showcase brief from the completed agent context."""

        if context.repository_snapshot is None:
            raise ValueError("PresenterAgent 需要先生成 context.repository_snapshot。")

        snapshot = context.repository_snapshot
        brief = ShowcaseBrief(
            headline="DevOrbit：本地多 Agent 代码评审助手",
            summary=(
                "DevOrbit 展示了面向开发者的 Agent 工作流：扫描仓库、协同评审/修复/测试角色，"
                "并在离线可运行的前提下生成可分享报告。"
            ),
            demo_metrics={
                "scanned_files": str(snapshot.file_count),
                "scanned_lines": str(snapshot.total_lines),
                "findings": str(len(context.discovered_issues)),
                "provider": "mock 演示",
            },
            honesty_note=(
                "本摘要中的所有指标都来自本地扫描的演示运行，"
                "不代表生产使用量、收入或真实落地规模。"
            ),
        )
        context.raw_notes.append(brief.summary)
        self.log_step(
            context,
            action="生成展示摘要",
            prompt=(
                f"为 {snapshot.file_count} 个文件和 "
                f"{len(context.discovered_issues)} 个发现生成展示摘要。"
            ),
        )
        return brief
