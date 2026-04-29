# DevOrbit

DevOrbit is a local-first, multi-agent code review and auto-fix assistant for developers.

It scans a repository, understands the project shape, analyzes a Git diff or selected directory, and produces:

- diagnostic findings
- fix suggestions
- test suggestions
- a readable application/demo brief
- a Markdown report suitable for sharing

The current implementation ships with a deterministic `mock` LLM provider, so the full workflow runs without any real API key. Provider interfaces are prepared for OpenAI-compatible and MiMo-compatible APIs.

> Demo note: this repository may generate demo logs, demo reports, and placeholder metrics. They are explicitly marked as demo artifacts and must not be represented as real users, revenue, production traffic, or commercial impact.

## Why DevOrbit

DevOrbit is built to demonstrate an Agent/AI-driven developer tool rather than a single-purpose script:

- A scanner agent maps repository structure and target files.
- A reviewer agent identifies quality, reliability, and maintainability issues.
- A fixer agent proposes precise patches and safer implementation routes.
- A test strategist agent recommends validation steps.
- A presenter agent turns the work into human-readable review material.
- A workflow orchestrator records agent traces and closes the loop with reports.

This makes it suitable as a project artifact for the Xiaomi MiMo Orbit creator incentive application, while staying honest about demo status and local limitations.

## Quick Start

```bash
python -m pip install -e ".[dev]"
devorbit --help
devorbit review --path examples/sample_project --output artifacts/demo_report.md
```

If dependencies are already installed, you can also run:

```bash
python -m devorbit.cli review --path examples/sample_project
```

## CLI

```bash
devorbit review --path . --mode directory --provider mock --output artifacts/report.md
devorbit inspect --path .
devorbit providers
```

### Commands

- `review`: run the multi-agent review workflow.
- `inspect`: print a repository scan summary.
- `providers`: show configured provider options.

## Provider Roadmap

DevOrbit currently includes:

- `mock`: deterministic offline provider for tests and demos.
- `openai-compatible`: interface placeholder for OpenAI-compatible chat completion APIs.
- `mimo-compatible`: interface placeholder for future MiMo-compatible endpoints.

Real provider calls are intentionally not enabled by default. Add API keys through environment variables or explicit configuration only when implementing a production provider.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
```

The package targets Python 3.11+ and uses Typer, Pydantic, Rich, and pytest.

## Repository Layout

```text
DevOrbit/
  src/devorbit/       Python package
  tests/              pytest tests
  examples/           small demo repositories and inputs
  docs/               design and application notes
  artifacts/          generated demo reports and logs
```

## License

MIT

