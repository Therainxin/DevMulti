from typer.testing import CliRunner

from devorbit.cli import app


runner = CliRunner()


def test_providers_command() -> None:
    result = runner.invoke(app, ["providers"])

    assert result.exit_code == 0
    assert "mock" in result.output
    assert "mimo-compatible" in result.output


def test_review_command_writes_report(tmp_path) -> None:
    output = tmp_path / "report.md"
    result = runner.invoke(
        app,
        ["review", "--path", "examples/sample_project", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "演示说明" in content
    assert "Agent 工作流" in content
