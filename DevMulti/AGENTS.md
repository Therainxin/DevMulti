# AGENTS.md

## Project Goal

DevOrbit is a local-first multi-agent code review and auto-fix assistant. It should scan local repositories, analyze Git diffs or selected directories, generate diagnostic reports, propose fixes, suggest tests, and produce readable showcase material for developer-facing demos and application submissions.

The project must feel like an Agent/AI workflow:

- multiple agents with clear responsibilities
- explicit orchestration and trace records
- tool-style repository scanning
- deterministic Mock LLM provider for offline runs
- extensible provider interface for OpenAI-compatible and MiMo-compatible APIs
- tests that verify the workflow loop

## Coding Standards

- Use Python 3.11+.
- Keep package code under `src/devorbit/`.
- Use Typer for CLI commands.
- Use Pydantic for shared data contracts.
- Use Rich for screenshot-friendly terminal output.
- Keep functions small and named around workflow responsibilities.
- Prefer deterministic behavior in tests and demo mode.
- Avoid hidden network calls. The default workflow must run offline.
- Do not commit local secrets, API keys, `.env` files, or private repository contents.

## Test Command

```bash
pytest
```

Run focused tests when changing a narrow area, but every new feature must be covered by pytest tests before it is considered complete.

## Data Honesty Rule

Do not fabricate real impact data.

Allowed:

- demo logs
- demo reports
- placeholder metrics
- synthetic examples
- clearly labeled mock provider output

Not allowed:

- fake production users
- fake revenue
- fake enterprise deployments
- fake benchmark wins
- fake model usage or token consumption
- fake customer testimonials

Any generated artifact with metrics must clearly state that the values are demo or placeholder data unless backed by real evidence.

## Feature Rule

Any new feature must include tests. If a feature changes CLI behavior, add or update CLI tests. If a feature changes report content, test the generated data model or Markdown output.

## CLI Presentation Rule

CLI output should be suitable for screenshots:

- use clear section titles
- keep terminal output readable at normal widths
- prefer Rich tables, panels, and status messages
- avoid noisy stack traces for expected user errors
- label demo/mock output clearly

