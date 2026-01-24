# blawx-mcp

A minimal run-local MCP server (SSE over HTTP) that calls the Blawx app API using an API key from the environment.

## Prereqs

- Python 3.10+

## Install

From this repo root:

```bash
python -m pip install -e .
```

## Configuration

Set required configuration in your environment:

```bash
export BLAWX_API_KEY="your_key_here"
export BLAWX_TEAM_SLUG="your_team_slug"
export BLAWX_PROJECT_ID="42"
```

Optional override:

- `BLAWX_BASE_URL` (default: `https://app.blawx.dev`)

## Run

Run the MCP server from this folder (no install required):

```bash
./.venv/bin/python -m blawx_mcp
```

Defaults:

- Binds to `127.0.0.1:8765`
- SSE endpoint at `http://127.0.0.1:8765/sse`

Optional server bind overrides:

```bash
export BLAWX_MCP_HOST="127.0.0.1"
export BLAWX_MCP_PORT="8765"
```

## Tools

- `blawx_health`: calls `GET /health` on the Blawx app API and returns status + body.
- `blawx_ontology_list`: calls `GET /api/teams/{team_id}/projects/{project_id}/ontology/`.
- `blawx_ontology_category_detail`: calls `GET /api/teams/{team_id}/projects/{project_id}/ontology/categories/{category_id}/`.
- `blawx_ontology_relationship_detail`: calls `GET /api/teams/{team_id}/projects/{project_id}/ontology/relationships/{relationship_id}/`.
- `blawx_fact_scenarios_list`: calls `GET /api/teams/{team_id}/projects/{project_id}/facts/`.
- `blawx_fact_scenario_detail`: calls `GET /api/teams/{team_id}/projects/{project_id}/facts/{fact_scenario_id}/`.
- `blawx_questions_list`: calls `GET /api/teams/{team_id}/projects/{project_id}/questions/shared/`.
- `blawx_question_detail`: calls `GET /api/teams/{team_id}/projects/{project_id}/questions/shared/{question_id}/`.

Reasoner workflow (cache-key based):

- `blawx_question_ask_with_facts`: calls `POST /a/{team_slug}/project/{proj}/questions/{question}/ask/` and returns:
	- `cache_key` (string)
	- optional metadata when available: `ttl_seconds`, `created_at`, `answer_count`
- `blawx_question_ask_with_fact_scenario`: calls `POST /a/{team_slug}/project/{proj}/questions/{question}/ask/qfa/` and returns the same shape.

Cached responses can expire. If retrieval tools return `status_code` 410, re-run an ask tool to obtain a fresh `cache_key`.

- `blawx_list_answers`: calls `GET /a/{team_slug}/project/{proj}/questions/{question}/responses/{cache_key}/answers/` and returns:
	- `total` (int)
	- `answers` (list of objects): `{ answer_index: int, bindings: str, explanation_count: int }`

- `blawx_list_explanations`: calls `GET /a/{team_slug}/project/{proj}/questions/{question}/responses/{cache_key}/answers/{answer_index}/` and returns:
	- `answer_index` (int)
	- `bindings` (str)
	- `explanations` (list): `{ explanation_index: int, parts_available: ["model"|"attributes"|"explanation"] }`

Part retrieval tools call `GET /a/{team_slug}/project/{proj}/questions/{question}/responses/{cache_key}/answers/{answer_index}/explanations/{explanation_index}/{part_name}/`.
They support optional `start` / `end` query params that are 1-based and inclusive (line slicing):

- `blawx_get_model_part`
- `blawx_get_attributes_part`
- `blawx_get_explanation_part`

Each returns an object shaped like:

- `part`: one of `model` | `attributes` | `explanation`
- `type`: optional string (nullable)
- `start`, `end`, `total`: optional integers (nullable)
- `data`: string (the newline-joined text for that part)

Important: interpret the explanation alongside attributes. The explanation part may use variables whose meaning depends on constraints described in the attributes part; reading explanation without attributes can be misleading.
