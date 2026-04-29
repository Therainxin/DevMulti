"""Repository scanning helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

from devorbit.models import FileSummary, RepositorySnapshot, ReviewMode

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "artifacts",
    "build",
    "dist",
    "node_modules",
}

LANGUAGE_BY_SUFFIX = {
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".md": "Markdown",
    ".py": "Python",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".yml": "YAML",
    ".yaml": "YAML",
}


def detect_language(path: Path) -> str:
    """Return a display language for a path."""

    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "Text")


def scan_repository(root: Path, mode: ReviewMode = ReviewMode.DIRECTORY) -> RepositorySnapshot:
    """Scan a repository-like directory into a lightweight snapshot."""

    resolved = root.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Path does not exist: {resolved}")
    if not resolved.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {resolved}")

    files: list[FileSummary] = []
    ignored: set[str] = set()

    for path in sorted(resolved.rglob("*")):
        relative_parts = path.relative_to(resolved).parts
        ignored_part = next((part for part in relative_parts if part in IGNORED_DIRECTORIES), None)
        if ignored_part:
            ignored.add(ignored_part)
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(resolved).as_posix()
        files.append(
            FileSummary(
                path=relative,
                language=detect_language(path),
                line_count=len(text.splitlines()),
                size_bytes=path.stat().st_size,
            )
        )

    return RepositorySnapshot(
        root=str(resolved),
        mode=mode,
        files=files,
        target_paths=[str(resolved)],
        ignored_directories=sorted(ignored),
    )


def get_git_diff(root: Path) -> str:
    """Return the current Git diff, or an empty string outside Git repositories."""

    try:
        completed = subprocess.run(
            ["git", "diff", "--", "."],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""
    if completed.returncode != 0:
        return ""
    return completed.stdout
