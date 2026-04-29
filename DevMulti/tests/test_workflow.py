from pathlib import Path

from devorbit.models import ProviderName, ReviewMode
from devorbit.workflow import run_review


def test_mock_workflow_runs_on_sample_project() -> None:
    report = run_review(
        path=Path("examples/sample_project"),
        mode=ReviewMode.DIRECTORY,
        provider_name=ProviderName.MOCK,
    )

    assert report.demo is True
    assert report.provider == ProviderName.MOCK
    assert report.repository.file_count >= 1
    assert report.issues
    assert report.fixes
    assert report.tests
    assert len(report.traces) == 6
    assert "demo" in report.showcase.honesty_note.lower()
