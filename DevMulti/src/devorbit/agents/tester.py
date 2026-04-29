"""Test strategist agent."""

from __future__ import annotations

from devorbit.agents.base import BaseAgent
from devorbit.context import AgentContext
from devorbit.models import TestPlan


class TestStrategistAgent(BaseAgent):
    """Plan validation steps for proposed fixes."""

    name = "test_strategist"
    role = "回归测试与验证规划"

    def run(self, context: AgentContext) -> AgentContext:
        """Create a test plan from discovered issues and fix suggestions."""

        focus_areas = sorted(
            {
                issue.category.value
                for issue in context.discovered_issues
                if issue.category is not None
            }
        )
        regression_tests = [
            f"为该问题补充回归覆盖：{issue.title}"
            for issue in context.discovered_issues
            if issue.severity.value in {"medium", "high", "critical"}
        ]
        context.test_plan = TestPlan(
            summary="运行现有测试套件，并为变更行为补充聚焦回归覆盖。",
            commands=["pytest"],
            focus_areas=focus_areas or ["maintainability"],
            regression_tests=regression_tests,
            rationale="测试闭环应证明评审驱动的修复保持原有行为，并覆盖已报告风险。",
        )
        self.log_step(
            context,
            action="规划测试",
            prompt=(
                f"为 {len(context.discovered_issues)} 个问题和 "
                f"{len(context.fix_suggestions)} 条修复建议准备验证计划。"
            ),
        )
        return context
