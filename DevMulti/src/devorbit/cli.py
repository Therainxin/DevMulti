"""Typer CLI for DevOrbit."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from devorbit.models import ProviderName, ReviewMode
from devorbit.repository import scan_repository
from devorbit.workflow import run_review

app = typer.Typer(
    name="devorbit",
    help="面向开发者的多 Agent 代码评审与自动修复助手。",
    no_args_is_help=True,
)
console = Console()

SEVERITY_LABELS = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "critical": "严重",
}


def _provider_option() -> ProviderName:
    return ProviderName.MOCK


@app.command()
def providers() -> None:
    """查看可用的 LLM Provider。"""

    table = Table(title="DevOrbit Provider 列表")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("状态", style="green")
    table.add_column("说明")
    table.add_row("mock", "可用", "离线、稳定、可测试的演示 Provider，不需要 API Key。")
    table.add_row("openai-compatible", "预留", "OpenAI-compatible 接口占位，后续可接真实模型。")
    table.add_row("mimo-compatible", "预留", "MiMo-compatible 接口占位，后续可接真实模型。")
    console.print(table)


@app.command()
def inspect(
    path: Annotated[Path, typer.Option("--path", "-p", help="要查看的仓库或目录。")] = Path("."),
) -> None:
    """查看仓库结构摘要。"""

    snapshot = scan_repository(path)
    table = Table(title=f"仓库快照：{Path(snapshot.root).name}")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="white")
    table.add_row("根目录", snapshot.root)
    table.add_row("文件数", str(snapshot.file_count))
    table.add_row("代码行数", str(snapshot.total_lines))
    table.add_row("已跳过目录", ", ".join(snapshot.ignored_directories) or "无")
    console.print(table)


@app.command()
def review(
    path: Annotated[Path, typer.Option("--path", "-p", help="要评审的仓库或目录。")] = Path("."),
    mode: Annotated[
        ReviewMode,
        typer.Option("--mode", "-m", help="评审模式：directory 或 diff。"),
    ] = ReviewMode.DIRECTORY,
    provider: Annotated[
        ProviderName,
        typer.Option("--provider", help="要使用的 LLM Provider。"),
    ] = ProviderName.MOCK,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="可选的 Markdown 报告输出路径。"),
    ] = None,
) -> None:
    """运行多 Agent 代码评审工作流。"""

    if provider != ProviderName.MOCK:
        raise typer.BadParameter("当前离线版本只支持 mock Provider。")

    with console.status("[bold cyan]正在运行 DevOrbit 多 Agent 工作流...[/bold cyan]"):
        report = run_review(path=path, mode=mode, provider_name=provider)

    console.print(
        Panel.fit(
            f"[bold]DevOrbit 评审完成[/bold]\n"
            f"项目：[cyan]{report.project_name}[/cyan]\n"
            f"Provider：[green]{report.provider.value}[/green]（演示模式）\n"
            f"文件：{report.repository.file_count} | 行数：{report.repository.total_lines} | 问题：{len(report.issues)}",
            title="多 Agent 评审",
            border_style="cyan",
        )
    )

    findings = Table(title="发现的问题")
    findings.add_column("严重级别", style="magenta", no_wrap=True)
    findings.add_column("问题", style="white")
    findings.add_column("位置", style="cyan")
    for issue in report.issues:
        findings.add_row(SEVERITY_LABELS.get(issue.severity.value, issue.severity.value), issue.title, issue.file_path or "工作区")
    console.print(findings)

    trace = Table(title="Agent 执行记录")
    trace.add_column("Agent", style="cyan", no_wrap=True)
    trace.add_column("动作", style="green")
    trace.add_column("观察结果")
    for item in report.traces:
        trace.add_row(item.agent_name, item.action, escape(item.observation))
    console.print(trace)

    if output:
        written = report.write_markdown(output)
        console.print(f"[bold green]报告已写入：[/bold green] {written}")
    else:
        console.print("[yellow]未提供 --output 路径；报告仅保留在内存中。[/yellow]")


if __name__ == "__main__":
    app()
