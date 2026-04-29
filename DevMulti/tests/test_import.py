from devorbit import ReviewReport, run_review


def test_public_imports() -> None:
    assert ReviewReport.__name__ == "ReviewReport"
    assert callable(run_review)

