"""Deterministic offline LLM provider for tests and demos."""

from __future__ import annotations

import hashlib
import re

from devorbit.llm.provider import LLMProvider


class MockLLMProvider(LLMProvider):
    """Stable provider that mimics code review reasoning without network calls."""

    name = "mock"

    def generate(self, prompt: str) -> str:
        """Return deterministic, review-like text based on the prompt intent."""

        normalized = prompt.lower()
        digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:8]

        if "architecture" in normalized or "entrypoint" in normalized or "core module" in normalized or "架构" in prompt:
            body = (
                "架构摘要已生成：已识别可能的入口文件、核心模块、测试位置、依赖信号，"
                "以及需要重点复查的风险区域。"
            )
        elif (
            re.search(r"\breport\b", normalized)
            or "write markdown" in normalized
            or "render markdown" in normalized
            or "报告" in prompt
        ):
            body = (
                "报告草稿已生成：内容按截图展示场景组织，包含项目概览、Agent 工作流、"
                "问题发现、修复建议和验证计划。"
            )
        elif "scan" in normalized or "repository" in normalized or "扫描" in prompt or "仓库" in prompt:
            body = (
                "仓库扫描完成：已识别评审范围、统计源码文件，并区分人工编写代码与应跳过目录。"
            )
        elif "test" in normalized or "validation" in normalized or "测试" in prompt or "验证" in prompt:
            body = (
                "验证计划已生成：建议运行现有测试套件，补充聚焦的回归测试，"
                "并加入一条覆盖用户主流程的冒烟命令。"
            )
        elif "fix" in normalized or "patch" in normalized or "修复" in prompt or "补丁" in prompt:
            body = (
                "修复策略已生成：优先采用保持行为不变的最小补丁；条件允许时先补回归测试，"
                "并将改动限制在受影响模块内。"
            )
        elif "showcase" in normalized or "brief" in normalized or "application" in normalized:
            body = (
                "展示摘要已生成：重点呈现多 Agent 编排、工具调用、离线可复现能力，"
                "并明确标注演示指标。"
            )
        else:
            body = (
                "评审分析已完成：已从正确性、可维护性、测试缺口和运行风险角度检查，"
                "并按开发影响对问题排序。"
            )

        return f"[mock:{digest}] {body}"
