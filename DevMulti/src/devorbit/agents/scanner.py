"""Repository scanner agent."""

from __future__ import annotations

from devorbit.agents.base import BaseAgent
from devorbit.context import AgentContext
from devorbit.models import ReviewMode
from devorbit.repository import scan_repository


class ScannerAgent(BaseAgent):
    """Map repository structure before review begins."""

    name = "scanner"
    role = "Repository structure and target discovery"

    def run(self, context: AgentContext) -> AgentContext:
        """Scan the repository and store a snapshot on the context."""

        snapshot = scan_repository(context.repo_path, mode=ReviewMode.DIRECTORY)
        snapshot.target_paths = context.normalized_targets()
        context.repository_snapshot = snapshot
        self.log_step(
            context,
            action="scan_repository",
            prompt=(
                f"Scan repository at {context.repo_path}. "
                f"Targets: {', '.join(context.normalized_targets())}. "
                f"Found {snapshot.file_count} files and {snapshot.total_lines} lines."
            ),
        )
        return context

