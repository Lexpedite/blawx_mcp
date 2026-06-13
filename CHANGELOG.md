# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows Semantic Versioning.

## [0.7.1c] - 2026-06-13

### Fixed
- Guaranteed a minimum frame height for both MCP App viewers (`ui/answer_viewer.html`, `ui/code_viewer.html`) in claude.ai. The 0.7.1b measurement-and-write approach ran too late: claude.ai snapshots the `documentElement` height early, so writing it from JS after the first paint (before async answers/Blockly render) couldn't reliably set a floor. Each viewer now carries a fixed `min-height` written inline on the `<html>` element itself — present at parse time, on the exact element claude.ai measures, in fixed px rather than viewport units (which create a circular sizing dependency in a small iframe). The post-render measurement and `ui/notifications/size-changed` post remain to grow the frame and serve spec-compliant hosts.

## [0.7.1b] - 2026-06-08

### Fixed
- Fixed the vertical sizing of both MCP App viewers (`ui/answer_viewer.html`, `ui/code_viewer.html`) in claude.ai, which would lock the iframe at a tiny height. claude.ai diverges from the MCP Apps spec: rather than resizing on `ui/notifications/size-changed` notifications, it reads the app's `documentElement` height directly off the DOM. Both viewers now measure their rendered content and write the height onto `<html>` themselves, and a `ResizeObserver` keeps the frame in step as content changes (answers/parts expand; Blockly resizes). The spec-compliant `ui/notifications/size-changed` post is still sent for hosts that honour it.

### Notes
- The `documentElement.style.height` workaround in both viewers is **temporary**, tracked as `anthropics/claude-ai-mcp` issue #69. It is marked `TEMPORARY WORKAROUND` in the source and can be removed once claude.ai resizes app iframes per the spec; the `ui/notifications/size-changed` path should remain.

## [0.7.0] - 2026-06-07

### Added
- Added `blawx_view_code`, a read-only Blawx code viewer MCP App that renders an arbitrary `blawx_json` workspace as Blawx blocks (no toolbox, drawers, code generation, or editing). The `blawx_json` can be agent-authored or taken from the `body` of `blawx_question_detail`, `blawx_fact_scenario_detail`, or `blawx_encodingpart_get`.
- Added the self-contained `ui://blawx/code-viewer` MCP App resource. The Blockly runtime (vendored under `ui/vendor/blockly/`) and the Blawx block definitions (`ui/viewer-bundle.js`, generated from the `blawx_saas` repo) are inlined at serve time, so the viewer needs no network access to render.
- Added tests covering the viewer tool's UI metadata, workspace pass-through, input validation, resource self-containment, and asset packaging.

### Changed
- Extended `[tool.setuptools.package-data]` to ship the viewer bundle and vendored Blockly assets, and bumped the version to `0.7.0`.

## [0.6.0] - 2026-06-02

### Added
- Added the Blawx answer viewer MCP App: the `blawx_view_answers` tool and the `ui://blawx/answers` resource (`ui/answer_viewer.html`), which let users interactively explore a cached question response — answers, bindings, and nested explanations — directly in MCP Apps hosts.
- Added structured NiceTree explanations: `blawx_get_explanation_part` returns the explanation as a `{conclusion, reasons}` tree, and the ask tools default to `output_styles = ["human", "scasp"]` so both human-readable and structured parts are available.
- Added in-app model context sharing: content the user opens in the answer viewer is mirrored back into the model context via the standard MCP Apps `ui/update-model-context` request.
- Added tests covering the answer viewer's UI metadata, the cached-response result shape, structured NiceTree parsing, and link absolutization.

### Changed
- Reshaped the ask tools (`blawx_question_ask_with_fact_scenario`, `blawx_question_ask_with_facts`) and `blawx_view_answers` to return a `CallToolResult` carrying MCP Apps UI metadata (`_meta.ui`) so supporting hosts render the viewer, while non-app hosts still receive readable structured content.
- Absolutized root-relative legislation links in model and explanation parts against the configured Blawx base URL so they resolve from any client.

## [0.5.0] - 2026-05-17

### Added
- Added `blawx_declared_objects_list` so agents can inspect declared object symbols and trace them back to source legal text before writing facts, questions, or encodings.
- Added `workflow_hint` and `next_recommended_tool` fields on structured discovery and legal-document responses so clients get explicit guidance about the next MCP call.
- Added tests covering compact response envelopes, text-only MCP content tools, declared-object discovery, and removal of redundant read surfaces.

### Changed
- Pruned structured MCP tool responses to a compact envelope containing `status_code`, `ok`, and `body`, plus workflow guidance where relevant. Tool outputs no longer echo request URLs, headers, params, or submitted payloads back to the client.
- Changed `blawx_encoding_guide` to return guide markdown as MCP text content only, and changed `blawx_legaldocparts_list` to return the legal-document hierarchy as a Markdown text content block rather than structured JSON.
- Made `blawx_ontology_list` the primary ontology discovery surface and tightened README/guide guidance around using `blawx_legaldocparts_list` for hierarchy and `blawx_legaldocpart_detail` for full part fields.
- Tightened `project_id` validation so project-scoped tools consistently reject non-positive integers with the same error message.
- Bumped version to `0.5.0`.

### Removed
- Removed `blawx_project_detail` and the redundant ontology read helpers `blawx_ontology_categories_list`, `blawx_ontology_relationships_list`, `blawx_ontology_relationship_parameters_list`, and `blawx_ontology_relationship_parameter_detail` in favor of the consolidated discovery tools.

## [0.4.0] - 2026-04-26

### Added
- Added `blawx_teams_list` so agents can discover teams available to the configured API key before selecting a project.
- Added explicit `team_slug` arguments to project-scoped tools so hosted and local clients select teams at tool-call time instead of startup time.
- Added guidance across README, MCP tool help, and encoding/legal-doc guides instructing agents to use the only available team automatically, or ask the user which team to use when multiple teams are available.
- Added tests covering discovery tool signatures and explicit `team_slug` requirements for project-scoped tools.

### Changed
- Removed `BLAWX_TEAM_SLUG` from required environment configuration. `BLAWX_API_KEY` is now the only required startup setting.
- Updated hosted-consumer guidance so `Settings` carries only base URL and API key; team selection is provided through tool arguments.
- Bumped version to `0.4.0`.

### Notes
- Confirmed `GET https://app.blawx.dev/teams/api/teams/` exists on Blawx: unauthenticated requests return `403` with `{"detail":"Authentication credentials were not provided."}` rather than `404`.

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

## [0.2.1] - 2026-04-18

### Added
- Added project-listing and rules-management tooling (PR #2: Add projects and rules).

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
