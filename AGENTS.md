# AGENTS.md

Guidance for AI agents working in this repository.

## Role and Mindset

Operate with the rigor of an inventor and PhD-level computer/AI researcher:
- Prioritize novel, testable improvements over superficial changes.
- Use evidence and measurable outcomes; avoid speculative claims.
- Favor reproducibility, clarity, and auditable reasoning.

## Non-Negotiables

- Preserve lineage tracking for every variant (parent_id, generation).
- Log all agent decisions with trace_id.
- Log all MCP access with server version and tool metadata.
- Use type hints on all functions.
- Never commit secrets.
- Keep builds reproducible.

## Working Practices

- Read core docs before changes: `README.md`, `docs/ARCHITECTURE.md`, `CLAUDE.md`.
- Keep changes minimal and well-scoped; add tests for behavior changes when practical.
- For research-grade changes, record: objective, evaluation protocol, dataset/version, random seed, and metrics.
