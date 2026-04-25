# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.3.0] - 2026-04-25

### Added
- Added `settings_context()` in `config.py` to allow per-request `Settings` injection via `contextvars.ContextVar`. Hosted multi-tenant consumers can now inject per-user settings without touching environment variables.
- Exported `Settings`, `get_settings`, `settings_context`, and `mcp` from `blawx_mcp.__init__` as a stable public API.
- Added ADR at `docs/adr/0001-contextvars-settings.md` documenting the design decision.
- Added `pytest` test suite under `tests/` covering env-var path, settings injection, context isolation, and cache isolation.
- Added GitHub Actions CI workflow (`.github/workflows/tests.yml`) that runs `pytest` on push and pull request across Python 3.10–3.12.

### Changed
- `_TEAM_ID_CACHE` in `server.py` is now keyed by `(api_key, team_slug)` tuple instead of `team_slug` alone, preventing cross-user cache collisions in multi-tenant deployments.
- Bumped version to `0.3.0`.

## [0.2.0] - 2026-04-11

### Added
- Added a `--stdio` CLI flag so `blawx_mcp` can run as a local stdio MCP server for clients such as Claude Desktop.
- Added ontology management tools for categories, relationships, and relationship parameters, including create, update, delete, list, and detail operations.
- Added question and fact-scenario management tools for create, update, delete, and full-project listing workflows.
- Added legal-document navigation and encoding-part tools, including guidance for reading legislation text and updating encodings.
- Added guide-backed MCP help content for encoding workflow, Blawx JSON structure, ontology usage, s(CASP), and validated examples.
- Added cached-response metadata access and explanation-part retrieval helpers for follow-up analysis workflows.

### Changed
- Expanded request schemas so workspace write tools explicitly validate Blawx JSON payloads and named resources validate required name and slug fields.
- Hardened ask-tool behavior and documentation around cached responses, follow-up retrieval, and shared-question requirements.
- Packaged markdown guides with the distribution so guide content is available when the server is installed.

### Fixed
- Improved error guidance for Blawx JSON write failures by attaching next-step documentation hints and warning interpretation guidance.
- Corrected release-facing documentation wording and tool references for new workflows.

## [0.1.0] - 2026-04-11

### Added
- Initial public release of the local Blawx MCP server over SSE/HTTP for coding-agent integrations.
- Added environment-based configuration for Blawx API access, project selection, and local server bind settings.
- Added core project-discovery tools for health checks, shared questions, fact scenarios, and ontology inspection.
- Added ask tools for running questions with either stored fact scenarios or structured facts payloads.
- Added answer and explanation browsing tools, including model, attributes, explanation, and constraint-satisfaction parts.

### Notes
- This release established the basic read-oriented MCP workflow: discover project content, ask a question, then inspect answers and explanations.
