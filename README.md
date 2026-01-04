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

Set an API key in your environment:

```bash
export BLAWX_API_KEY="your_key_here"
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
- `blawx_lexpedite_project6_question7_ask`: calls `POST /a/lexpedite/project/42/questions/59/ask/qfa/` with JSON body `{"facts": <facts>}` (defaults to `32`).
