"""Fix suggestion agent."""

from __future__ import annotations

from devorbit.agents.base import BaseAgent
from devorbit.context import AgentContext
from devorbit.models import CodeIssue, FixSuggestion


class FixerAgent(BaseAgent):
    """Convert findings into scoped repair suggestions."""

    name = "fixer"
    role = "补丁规划与自动修复建议"

    def run(self, context: AgentContext) -> AgentContext:
        """Generate fix suggestions for discovered issues."""

        fixes = [
            FixSuggestion(
                issue_title=issue.title,
                summary=f"处理该问题：{issue.description}",
                patch_hint=self._patch_hint(issue),
                affected_files=[issue.file_path] if issue.file_path else [],
                confidence=0.72 if issue.file_path else 0.64,
                requires_human_review=True,
            )
            for issue in context.discovered_issues
        ]
        context.fix_suggestions = fixes
        self.log_step(
            context,
            action="生成修复建议",
            prompt=f"为 {len(context.discovered_issues)} 个评审发现生成修复建议。",
        )
        return context

    @staticmethod
    def _patch_hint(issue: CodeIssue) -> str:
        """Return a concise patch direction for one issue."""

        if issue.recommendation:
            return issue.recommendation
        if issue.file_path:
            return f"检查 {issue.file_path}，并采用保持行为不变的最小改动。"
        return "确认目标输入，然后补充缺失源码文件或缩小评审路径。"
