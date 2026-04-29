# DevOrbit Design Notes

DevOrbit is intentionally local-first. The initial implementation emphasizes workflow shape, traceability, and deterministic tests instead of pretending that a real hosted model is available.

## Agent Roles

- Scanner: maps repository files and basic language metadata.
- Reviewer: turns repository context into findings.
- Fixer: maps findings to repair suggestions.
- Test strategist: recommends validation commands and regression tests.
- Presenter: produces application/demo material with explicit honesty notes.

## Provider Strategy

The `mock` provider is the default and must remain fully offline. It lets contributors run demos, tests, and screenshots without secrets.

OpenAI-compatible and MiMo-compatible providers are reserved extension points. They should be implemented behind the same `LLMProvider` contract and covered with tests that do not require real network access by default.

## Demo Integrity

Generated artifacts can include demo metrics such as files scanned, findings generated, and provider mode. They must never claim production adoption, revenue, or customer impact unless backed by real evidence.

