from devorbit.llm.mock import MockLLMProvider


def test_mock_provider_is_deterministic() -> None:
    provider = MockLLMProvider()
    prompt = "Review repository for maintainability issues."

    assert provider.generate(prompt) == provider.generate(prompt)


def test_mock_provider_scan_prompt_mentions_repository_scan() -> None:
    output = MockLLMProvider().generate("Scan repository files and target paths.")

    assert "仓库扫描完成" in output
    assert output.startswith("[mock:")


def test_mock_provider_fix_prompt_mentions_small_patch() -> None:
    output = MockLLMProvider().generate("Suggest fix and patch strategy.")

    assert "最小补丁" in output


def test_mock_provider_test_prompt_mentions_validation_plan() -> None:
    output = MockLLMProvider().generate("Create a validation and test plan.")

    assert "验证计划已生成" in output
    assert "回归测试" in output


def test_mock_provider_review_prompt_mentions_prioritized_findings() -> None:
    output = MockLLMProvider().generate("Analyze code for bugs.")

    assert "评审分析已完成" in output
    assert "问题排序" in output
