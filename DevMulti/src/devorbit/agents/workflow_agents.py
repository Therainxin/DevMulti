"""Concrete agents used by the DevOrbit multi-agent workflow."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from devorbit.agents.base import BaseAgent
from devorbit.context import AgentContext
from devorbit.models import (
    AgentRunReport,
    ArchitectureSummary,
    CodeIssue,
    FileSummary,
    FixSuggestion,
    IssueCategory,
    ProviderName,
    RepositorySnapshot,
    ReviewMode,
    Severity,
    ShowcaseBrief,
    TestPlan,
)

IGNORED_DIRECTORIES = {".git", "node_modules", ".venv", "dist", "build", "__pycache__"}
DEPENDENCY_FILES = {
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "Pipfile",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "go.mod",
}
LANGUAGE_BY_SUFFIX = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".md": "Markdown",
    ".toml": "TOML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".go": "Go",
    ".rs": "Rust",
}
CODE_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"}
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]"
)


class RepoScannerAgent(BaseAgent):
    """Scan the target repository and produce a ``RepositorySnapshot``."""

    name = "repo_scanner"
    role = "仓库扫描与依赖识别"

    def run(self, context: AgentContext) -> AgentContext:
        """Collect file tree, languages, framework hints, and dependency files."""

        root = context.repo_path.resolve()
        if not root.exists():
            raise FileNotFoundError(f"仓库路径不存在：{root}")
        if not root.is_dir():
            raise NotADirectoryError(f"仓库路径不是目录：{root}")

        files: list[FileSummary] = []
        file_tree: list[str] = []
        ignored: set[str] = set()
        languages: Counter[str] = Counter()
        dependency_files: list[str] = []
        entrypoints: list[str] = []
        test_directories: set[str] = set()
        risk_areas: set[str] = set()

        for path in sorted(root.rglob("*")):
            relative_path = path.relative_to(root)
            parts = relative_path.parts
            ignored_part = next((part for part in parts if part in IGNORED_DIRECTORIES), None)
            if ignored_part:
                ignored.add(ignored_part)
                continue

            display_path = relative_path.as_posix()
            if path.is_dir():
                file_tree.append(f"{display_path}/")
                if self._is_test_path(display_path):
                    test_directories.add(parts[0])
                continue

            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            language = LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "Text")
            languages[language] += 1
            is_dependency = path.name in DEPENDENCY_FILES
            is_test = self._is_test_path(display_path)
            is_entrypoint = self._is_entrypoint(path, display_path)

            if is_dependency:
                dependency_files.append(display_path)
            if is_test and parts:
                test_directories.add(parts[0])
            if is_entrypoint:
                entrypoints.append(display_path)
            if "legacy" in display_path.lower() or "experimental" in display_path.lower():
                risk_areas.add(display_path)

            file_tree.append(display_path)
            files.append(
                FileSummary(
                    path=display_path,
                    language=language,
                    line_count=len(text.splitlines()),
                    size_bytes=path.stat().st_size,
                    sha1=hashlib.sha1(text.encode("utf-8")).hexdigest(),
                    is_test=is_test,
                    is_dependency_file=is_dependency,
                    is_entrypoint=is_entrypoint,
                )
            )

        frameworks = self._detect_frameworks(root, dependency_files)
        snapshot = RepositorySnapshot(
            root=str(root),
            mode=ReviewMode.DIRECTORY,
            files=files,
            file_tree=file_tree,
            languages=dict(sorted(languages.items())),
            frameworks=frameworks,
            dependency_files=dependency_files,
            entrypoints=entrypoints,
            test_directories=sorted(test_directories),
            risk_areas=sorted(risk_areas),
            target_paths=context.normalized_targets(),
            ignored_directories=sorted(ignored),
        )
        context.repository_snapshot = snapshot
        self.log_step(
            context,
            action="扫描仓库",
            prompt=(
                f"扫描仓库 {root}。文件数={snapshot.file_count}，"
                f"语言分布={snapshot.languages}，依赖文件={dependency_files}。"
            ),
        )
        return context

    @staticmethod
    def _is_test_path(path: str) -> bool:
        return path.startswith("tests/") or "/tests/" in path or Path(path).name.startswith("test_")

    @staticmethod
    def _is_entrypoint(path: Path, display_path: str) -> bool:
        return path.name in {"main.py", "app.py", "cli.py", "manage.py"} or display_path in {
            "src/main.py",
            "src/app.py",
            "index.js",
            "src/index.ts",
        }

    @staticmethod
    def _detect_frameworks(root: Path, dependency_files: list[str]) -> list[str]:
        frameworks: set[str] = set()
        package_json = root / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text(encoding="utf-8"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for name in ("react", "vue", "next", "express", "vite"):
                    if name in deps:
                        frameworks.add(name)
            except (json.JSONDecodeError, OSError):
                frameworks.add("JavaScript")

        for dep in dependency_files:
            if dep.endswith(".toml") or dep.startswith("requirements"):
                content = (root / dep).read_text(encoding="utf-8", errors="ignore").lower()
                if "fastapi" in content:
                    frameworks.add("FastAPI")
                if "django" in content:
                    frameworks.add("Django")
                if "typer" in content:
                    frameworks.add("Typer")
                if "pytest" in content:
                    frameworks.add("pytest")
        return sorted(frameworks)


class ArchitectureReasonerAgent(BaseAgent):
    """Understand repository structure and summarize architecture safely."""

    name = "architecture_reasoner"
    role = "架构理解与风险区域识别"

    def run(self, context: AgentContext) -> AgentContext:
        """Infer entry files, core modules, tests, and risk areas from the snapshot."""

        snapshot = _require_snapshot(context)
        core_modules = self._core_modules(snapshot)
        risk_areas = sorted(set(snapshot.risk_areas + self._risk_areas(snapshot)))
        llm_observation = self.provider.generate(
            "Architecture analysis summary. "
            f"语言={snapshot.languages}。入口文件={snapshot.entrypoints}。"
            f"核心模块={core_modules}。测试目录={snapshot.test_directories}。风险区域={risk_areas}。"
        )
        context.architecture_summary = ArchitectureSummary(
            summary=(
                f"仓库共扫描 {snapshot.file_count} 个文件，主要语言为"
                f"{', '.join(snapshot.languages) or '未识别'}。候选入口文件："
                f"{', '.join(snapshot.entrypoints) or '未检测到'}。"
            ),
            entry_files=snapshot.entrypoints,
            core_modules=core_modules,
            test_directories=snapshot.test_directories,
            risk_areas=risk_areas,
            llm_observation=llm_observation,
        )
        context.raw_notes.append(context.architecture_summary.summary)
        self.log_step(
            context,
            action="分析架构",
            prompt=(
                "生成可读的架构摘要，不暴露隐藏推理过程。"
                f"核心模块={core_modules}；风险区域={risk_areas}。"
            ),
        )
        return context

    @staticmethod
    def _core_modules(snapshot: RepositorySnapshot) -> list[str]:
        modules: Counter[str] = Counter()
        for file in snapshot.files:
            parts = Path(file.path).parts
            if file.is_test or file.is_dependency_file or not parts or Path(file.path).suffix.lower() not in CODE_SUFFIXES:
                continue
            modules[parts[0]] += 1
        return [name for name, _ in modules.most_common(5)]

    @staticmethod
    def _risk_areas(snapshot: RepositorySnapshot) -> list[str]:
        risks: list[str] = []
        if not snapshot.test_directories:
            risks.append("未检测到测试目录")
        for file in snapshot.files:
            if file.line_count > 300:
                risks.append(f"大文件：{file.path}")
        return risks


class IssueDiagnosisAgent(BaseAgent):
    """Diagnose code issues using deterministic rules plus provider summaries."""

    name = "issue_diagnosis"
    role = "静态规则诊断与 LLM 摘要"

    def run(self, context: AgentContext) -> AgentContext:
        """Scan code content and populate ``CodeIssue`` objects."""

        snapshot = _require_snapshot(context)
        root = Path(snapshot.root)
        issues: list[CodeIssue] = []

        for file in snapshot.files:
            if Path(file.path).suffix.lower() not in CODE_SUFFIXES:
                continue
            path = root / file.path
            text = path.read_text(encoding="utf-8", errors="ignore")
            issues.extend(self._scan_file(file.path, text))

        source_files = [file for file in snapshot.files if Path(file.path).suffix.lower() in CODE_SUFFIXES and not file.is_test]
        if source_files and not snapshot.test_directories:
            issues.append(
                CodeIssue(
                    title="缺少测试目录",
                    description="发现了源代码文件，但没有检测到 tests 目录或测试文件。",
                    severity=Severity.MEDIUM,
                    category=IssueCategory.TESTING,
                    evidence=f"检测到 {len(source_files)} 个源代码文件，但未发现测试套件。",
                    recommendation="在 tests/ 下补充覆盖主流程和高风险分支的聚焦测试。",
                    agent=self.name,
                )
            )

        llm_note = self.provider.generate(
            f"Review diagnosis: 静态规则在 {snapshot.file_count} 个文件中发现 {len(issues)} 个问题。"
        )
        context.raw_notes.append(llm_note)
        context.discovered_issues = issues
        self.log_step(
            context,
            action="诊断问题",
            prompt=f"使用静态规则诊断代码问题，并总结 {len(issues)} 个发现。",
        )
        return context

    def _scan_file(self, file_path: str, text: str) -> list[CodeIssue]:
        issues: list[CodeIssue] = []
        lines = text.splitlines()

        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("except:") or stripped.startswith("except Exception") or stripped.startswith("except BaseException"):
                issues.append(
                    self._issue(
                        "异常捕获范围过宽",
                        "过宽的异常捕获可能掩盖真实失败，让调试更困难。",
                        Severity.MEDIUM,
                        IssueCategory.BUG,
                        file_path,
                        index,
                        stripped,
                        "改为捕获具体异常类型，并保留有用的错误上下文。",
                    )
                )
            if SECRET_PATTERN.search(line):
                issues.append(
                    self._issue(
                        "疑似硬编码密钥或 Token",
                        "源码中直接出现了类似凭据的值。",
                        Severity.HIGH,
                        IssueCategory.SECURITY,
                        file_path,
                        index,
                        stripped,
                        "将密钥迁移到环境变量或密钥管理服务，并轮换已经暴露的值。",
                    )
                )
            if "TODO" in line or "FIXME" in line:
                issues.append(
                    self._issue(
                        "TODO/FIXME 技术债",
                        "生产代码中发现技术债标记。",
                        Severity.LOW,
                        IssueCategory.MAINTAINABILITY,
                        file_path,
                        index,
                        stripped,
                        "将该标记转为可跟踪任务，或在发布前解决。",
                    )
                )
            if re.search(r"\w+\[[^\]]+\]", line) and "len(" not in line and "try" not in line:
                issues.append(
                    self._issue(
                        "索引访问前缺少边界检查",
                        "代码在访问集合索引前，没有明显的长度或存在性检查。",
                        Severity.MEDIUM,
                        IssueCategory.BUG,
                        file_path,
                        index,
                        stripped,
                        "在索引访问前检查集合长度或键是否存在。",
                    )
                )

        if file_path.endswith(".py"):
            issues.extend(self._scan_python_functions(file_path, text))
        return issues

    @staticmethod
    def _scan_python_functions(file_path: str, text: str) -> list[CodeIssue]:
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return []

        issues: list[CodeIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = getattr(node, "end_lineno", node.lineno)
                length = end - node.lineno + 1
                branch_count = sum(
                    isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.Match))
                    for child in ast.walk(node)
                )
                if length > 50 or branch_count > 10:
                    issues.append(
                        CodeIssue(
                            title="函数过大或复杂度过高",
                            description="函数长度或分支数量偏高，可能难以评审和测试。",
                            severity=Severity.MEDIUM,
                            category=IssueCategory.MAINTAINABILITY,
                            file_path=file_path,
                            line=node.lineno,
                            line_end=end,
                            evidence=f"{node.name} 跨 {length} 行，包含 {branch_count} 个分支节点。",
                            recommendation="将函数拆分为更小的单元，并为关键分支补充聚焦测试。",
                            agent=IssueDiagnosisAgent.name,
                        )
                    )
        return issues

    @staticmethod
    def _issue(
        title: str,
        description: str,
        severity: Severity,
        category: IssueCategory,
        file_path: str,
        line: int,
        evidence: str,
        recommendation: str,
    ) -> CodeIssue:
        return CodeIssue(
            title=title,
            description=description,
            severity=severity,
            category=category,
            file_path=file_path,
            line=line,
            evidence=evidence,
            recommendation=recommendation,
            agent=IssueDiagnosisAgent.name,
        )


class FixPlannerAgent(BaseAgent):
    """Generate fix plans for diagnosed issues."""

    name = "fix_planner"
    role = "修复规划与补丁风险评估"

    def run(self, context: AgentContext) -> AgentContext:
        """Create one ``FixSuggestion`` for every issue."""

        suggestions: list[FixSuggestion] = []
        for issue in context.discovered_issues:
            suggestions.append(
                FixSuggestion(
                    issue_title=issue.title,
                    summary=issue.recommendation or f"修复问题：{issue.title}。",
                    patch_hint=self._patch_hint(issue),
                    affected_files=[issue.file_path] if issue.file_path else [],
                    risk_level=issue.severity,
                    confidence=self._confidence(issue),
                    requires_human_review=issue.severity in {Severity.HIGH, Severity.CRITICAL},
                )
            )
        context.fix_suggestions = suggestions
        self.log_step(
            context,
            action="规划修复",
            prompt=f"为 {len(suggestions)} 个问题生成修复计划，包含受影响文件和风险等级。",
        )
        return context

    @staticmethod
    def _patch_hint(issue: CodeIssue) -> str:
        if issue.category == IssueCategory.SECURITY:
            return "移除硬编码值，改为从环境变量或配置读取，并轮换已暴露密钥。"
        if issue.title == "异常捕获范围过宽":
            return "用具体异常类型替换宽泛捕获，并补充日志或重新抛出策略。"
        if issue.title == "索引访问前缺少边界检查":
            return "在访问前加入长度或键存在性判断，并定义空输入的兜底行为。"
        if issue.title == "函数过大或复杂度过高":
            return "抽取更小的辅助函数，并用回归测试保护原有行为。"
        if issue.category == IssueCategory.TESTING:
            return "新增测试文件，覆盖入口文件、边界场景和已报告的风险分支。"
        return issue.recommendation or "采用保持行为不变的最小补丁。"

    @staticmethod
    def _confidence(issue: CodeIssue) -> float:
        if issue.category in {IssueCategory.SECURITY, IssueCategory.TESTING}:
            return 0.86
        if issue.file_path:
            return 0.78
        return 0.68


class TestPlannerAgent(BaseAgent):
    """Plan verification commands and missing test coverage."""

    name = "test_planner"
    role = "测试命令与回归验证规划"

    def run(self, context: AgentContext) -> AgentContext:
        """Generate a ``TestPlan`` from issues, fixes, and dependency files."""

        snapshot = _require_snapshot(context)
        commands = self._available_commands(snapshot)
        missing_tests: list[str] = []
        if not snapshot.test_directories:
            missing_tests.append("创建 tests/ 目录，并为检测到的入口文件补充冒烟测试。")

        for issue in context.discovered_issues:
            if issue.file_path and issue.category in {IssueCategory.BUG, IssueCategory.SECURITY, IssueCategory.MAINTAINABILITY}:
                missing_tests.append(f"为 {issue.file_path} 补充回归测试：{issue.title}。")

        focus_areas = sorted({issue.category.value for issue in context.discovered_issues}) or ["smoke"]
        context.test_plan = TestPlan(
            summary="结合项目可用命令和定向回归测试验证修复效果。",
            commands=commands or ["pytest"],
            available_commands=commands,
            focus_areas=focus_areas,
            regression_tests=[
                f"验证 {', '.join(fix.affected_files) or '工作区'} 中「{fix.issue_title}」的修复。"
                for fix in context.fix_suggestions
            ],
            missing_tests=missing_tests,
            rationale="该计划结合现有项目工具链与问题级回归覆盖，避免修复引入新风险。",
        )
        self.log_step(
            context,
            action="规划测试",
            prompt=f"基于依赖文件 {snapshot.dependency_files} 和 {len(context.fix_suggestions)} 个修复建议规划测试。",
        )
        return context

    @staticmethod
    def _available_commands(snapshot: RepositorySnapshot) -> list[str]:
        commands: list[str] = []
        deps = set(snapshot.dependency_files)
        if "pyproject.toml" in deps or any(dep.startswith("requirements") for dep in deps):
            commands.append("pytest")
            commands.append("ruff check .")
            commands.append("mypy .")
        if "package.json" in deps:
            commands.append("npm test")
            commands.append("npm run lint")
        return commands


class ReportWriterAgent(BaseAgent):
    """Write the final Markdown report to ``artifacts/devorbit_report.md``."""

    name = "report_writer"
    role = "Markdown 报告生成"

    def run(self, context: AgentContext) -> AgentContext:
        """Render and write the final report from actual context data."""

        output_path = Path("artifacts/devorbit_report.md")
        self.log_step(
            context,
            action="写入报告",
            prompt=f"将包含 {len(context.discovered_issues)} 个问题的 Markdown 报告写入 {output_path.as_posix()}。",
        )
        report = build_run_report(context)
        report.write_markdown(output_path)
        context.raw_notes.append(f"报告已写入 {output_path.as_posix()}")
        return context


def build_run_report(context: AgentContext, provider_name: ProviderName = ProviderName.MOCK) -> AgentRunReport:
    """Build an ``AgentRunReport`` from the current context."""

    snapshot = context.repository_snapshot or RepositorySnapshot(root=str(context.repo_path.resolve()))
    test_plan = context.test_plan or TestPlan(
        summary="工作流尚未执行到测试规划。",
        commands=[],
        available_commands=[],
        focus_areas=[],
        regression_tests=[],
        missing_tests=[],
        rationale="前置 Agent 失败，测试规划未能完成。",
    )
    showcase = ShowcaseBrief(
        headline="DevOrbit 多 Agent 代码评审运行摘要",
        summary=(
            f"本次扫描 {snapshot.file_count} 个文件，诊断出 {len(context.discovered_issues)} 个问题，"
            f"并生成 {len(context.fix_suggestions)} 条修复建议。"
        ),
        demo_metrics={
            "scanned_files": str(snapshot.file_count),
            "scanned_lines": str(snapshot.total_lines),
            "issues": str(len(context.discovered_issues)),
            "agent_steps": str(len(context.agent_steps)),
        },
        honesty_note="以上指标来自本地演示运行，不代表真实生产影响力或商业落地数据。",
    )
    return AgentRunReport(
        project_name=Path(snapshot.root).name,
        provider=provider_name,
        mode=snapshot.mode,
        repository_snapshot=snapshot,
        architecture_summary=context.architecture_summary,
        discovered_issues=context.discovered_issues,
        fix_suggestions=context.fix_suggestions,
        test_plan=test_plan,
        agent_steps=context.agent_steps,
        showcase=showcase,
        demo=provider_name == ProviderName.MOCK,
    )


def _require_snapshot(context: AgentContext) -> RepositorySnapshot:
    if context.repository_snapshot is None:
        raise ValueError("执行该 Agent 前必须先生成 RepositorySnapshot。")
    return context.repository_snapshot
