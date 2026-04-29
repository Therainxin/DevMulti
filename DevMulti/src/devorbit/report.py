"""Markdown report rendering helpers."""

from __future__ import annotations

from collections import Counter

from devorbit.models import ReviewReport


SEVERITY_LABELS = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "严重",
}

CATEGORY_LABELS = {
    "bug": "缺陷",
    "security": "安全",
    "performance": "性能",
    "maintainability": "可维护性",
    "testing": "测试",
    "style": "风格",
    "documentation": "文档",
    "architecture": "架构",
}


def render_markdown(report: ReviewReport) -> str:
    """Render a DevOrbit run report as Chinese Markdown."""

    severity_counts = Counter(issue.severity.value for issue in report.issues)
    snapshot = report.repository_snapshot
    lines = [
        f"# DevOrbit 代码评审报告：{report.project_name}",
        "",
        "> 演示说明：本报告由本地扫描结果生成。Mock Provider 输出不代表真实模型调用、真实用户规模或生产影响力。",
        "",
        "## 项目概览",
        "",
        f"- Provider：`{report.provider.value}`",
        f"- 评审模式：`{report.mode.value}`",
        f"- 仓库根目录：`{snapshot.root}`",
        f"- 扫描文件数：`{snapshot.file_count}`",
        f"- 扫描行数：`{snapshot.total_lines}`",
        f"- 发现问题数：`{len(report.issues)}`",
        f"- 修复建议数：`{len(report.fixes)}`",
        "",
        "## 截图展示摘要",
        "",
        (
            f"DevOrbit 本次扫描 {snapshot.file_count} 个文件，涉及 "
            f"{', '.join(snapshot.languages) or '未识别语言'}，发现 "
            f"{len(report.issues)} 个问题，并生成 "
            f"{len(report.test_plan.commands)} 条测试命令建议。"
        ),
        "",
        "严重级别分布：",
    ]
    if severity_counts:
        for severity, count in sorted(severity_counts.items()):
            lines.append(f"- {SEVERITY_LABELS.get(severity, severity)}：`{count}`")
    else:
        lines.append("- 无：`0`")

    lines.extend(["", "## Agent 工作流", ""])
    for step in report.agent_steps:
        lines.append(f"- `{step.agent_name}` `{step.action}` `{step.status}`：{step.output_summary}")

    lines.extend(["", "## 仓库结构摘要", ""])
    lines.append("语言分布：")
    for language, count in snapshot.languages.items():
        lines.append(f"- {language}：`{count}` 个文件")
    if not snapshot.languages:
        lines.append("- 未检测到")

    lines.extend(["", "框架与依赖文件："])
    lines.append(f"- 框架：{', '.join(snapshot.frameworks) or '未检测到'}")
    lines.append(f"- 依赖文件：{', '.join(snapshot.dependency_files) or '未检测到'}")
    lines.append(f"- 入口文件：{', '.join(snapshot.entrypoints) or '未检测到'}")
    lines.append(f"- 测试目录：{', '.join(snapshot.test_directories) or '未检测到'}")
    lines.append(f"- 已跳过目录：{', '.join(snapshot.ignored_directories) or '无'}")

    lines.extend(["", "文件树节选："])
    for item in snapshot.file_tree[:40]:
        lines.append(f"- `{item}`")
    if len(snapshot.file_tree) > 40:
        lines.append(f"- ... 还有 `{len(snapshot.file_tree) - 40}` 项")

    lines.extend(["", "## 架构理解摘要", ""])
    if report.architecture_summary:
        arch = report.architecture_summary
        lines.extend(
            [
                arch.summary,
                "",
                f"- 入口文件：{', '.join(arch.entry_files) or '未检测到'}",
                f"- 核心模块：{', '.join(arch.core_modules) or '未检测到'}",
                f"- 测试目录：{', '.join(arch.test_directories) or '未检测到'}",
                f"- 风险区域：{', '.join(arch.risk_areas) or '未检测到'}",
                f"- LLM 摘要：{arch.llm_observation}",
            ]
        )
    else:
        lines.append("架构分析未完成。")

    lines.extend(["", "## 发现的问题", ""])
    if report.issues:
        for issue in report.issues:
            location = f"（{issue.file_path}" + (f":{issue.line}" if issue.line else "") + "）" if issue.file_path else ""
            severity = SEVERITY_LABELS.get(issue.severity.value, issue.severity.value)
            category = CATEGORY_LABELS.get(issue.category.value, issue.category.value)
            lines.extend(
                [
                    f"### [{severity}/{category}] {issue.title}{location}",
                    "",
                    issue.description,
                    "",
                    f"- 证据：{issue.evidence or '未提供'}",
                    f"- 建议：{issue.recommendation or '未提供'}",
                    "",
                ]
            )
    else:
        lines.append("当前工作流未检测到问题。")

    lines.extend(["", "## 修复建议", ""])
    if report.fixes:
        for fix in report.fixes:
            lines.extend(
                [
                    f"### {fix.issue_title}",
                    "",
                    f"- 修复思路：{fix.summary}",
                    f"- 受影响文件：{', '.join(fix.affected_files) or '工作区'}",
                    f"- 建议补丁摘要：{fix.patch_hint}",
                    f"- 风险等级：`{SEVERITY_LABELS.get(fix.risk_level.value, fix.risk_level.value)}`",
                    f"- 置信度：`{fix.confidence:.2f}`",
                    "",
                ]
            )
    else:
        lines.append("未生成修复建议。")

    lines.extend(["", "## 测试计划", "", report.test_plan.summary, ""])
    lines.append("建议执行命令：")
    for command in report.test_plan.commands:
        lines.append(f"- `{command}`")
    if not report.test_plan.commands:
        lines.append("- 未检测到可用命令")

    lines.extend(["", "重点验证方向："])
    for area in report.test_plan.focus_areas:
        lines.append(f"- {CATEGORY_LABELS.get(area, area)}")

    if report.test_plan.regression_tests:
        lines.extend(["", "回归测试建议："])
        for regression in report.test_plan.regression_tests:
            lines.append(f"- {regression}")

    if report.test_plan.missing_tests:
        lines.extend(["", "建议新增测试："])
        for missing in report.test_plan.missing_tests:
            lines.append(f"- {missing}")

    lines.extend(["", f"测试计划依据：{report.test_plan.rationale}", ""])

    lines.extend(
        [
            "## 运行备注",
            "",
            report.showcase.summary,
            "",
            "演示指标：",
        ]
    )
    for key, value in report.showcase.demo_metrics.items():
        lines.append(f"- {key}：`{value}`")
    lines.extend(["", f"真实性说明：{report.showcase.honesty_note}", ""])
    return "\n".join(lines)

