# blawx-mcp

A minimal run-local MCP server that calls the Blawx API using a Blawx API key.

## Prereqs

- Python 3.10+

## Install

From this repo root:

```bash
python -m pip install -e .
```

### Example: Windows + Claude Desktop

This is one way to set up the MCP server locally for Claude Desktop on Windows.

1. Clone the repository locally.

```powershell
git clone https://github.com/Lexpedite/blawx_mcp.git
cd blawx_mcp
```

2. Install the package.

```powershell
python -m pip install .
```

3. Find your team slug and project id from your Blawx project URL. The pattern is:

```text
https://app.blawx.dev/a/{team_slug}/project/{project_id}
```

4. Generate an API key from the Blawx profile page. In the left navigation bar, click "Profile", then use the "Add API Key" button. Copy the key when it is shown.

5. Add the MCP server to your Claude Desktop configuration file, typically at `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
	"mcpServers": {
		"blawx-mcp": {
			"command": "python",
			"args": ["-m", "blawx_mcp", "--stdio"],
			"env": {
				"BLAWX_API_KEY": "your API Key Here",
				"BLAWX_TEAM_SLUG": "your_team_name",
				"BLAWX_PROJECT_ID": "your_proj_number"
			}
		}
	}
}
```

You will need to completely quit Claude Desktop (using the Claude icon in the system tray and selecting "Quit", then restarting) and restart for 
the changes to your configuration to take effect.

## Configuration

Set required configuration in your environment:

```bash
export BLAWX_API_KEY="your_key_here"
export BLAWX_TEAM_SLUG="your_team_slug"
export BLAWX_PROJECT_ID="42"
```

You will find the Blawx Project ID and team slug in the URL of your
web browser when you go to the home page for your project. The
pattern will be
`https://app.blawx.dev/a/{team_slug}/project/{project_id}`

You can create a Blawx API Key if you have a Pro subscription to Blawx.
Click on "Profile" in the left navigation bar, and find the "Add API 
Key" button. When you click the button your API key will be displayed
only once at the top of the screen. Copy and paste it into your
environment settings.

## Run

Run the MCP server from this folder (no install required).

For SSE/HTTP transport:

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

For stdio transport, which is useful for local clients such as Claude Desktop:

```bash
./.venv/bin/python -m blawx_mcp --stdio
```

## Connect to Your Coding Agent

Coding agents differ in how they configure MCP servers. This is a typical
tool definition in your `mcp.json` for VS Code.

```
{
	"servers": {
		"my-blawx-sse-server": {
			"url": "http://127.0.0.1:8765/sse",
			"type": "http"
		}
	},
	"inputs": []
}
```

## Tools

These tools give your coding agent the following capabilities:

1. Discover what the project exposes (questions, fact scenarios, ontology).
2. Ask a question (using either a stored fact scenario or a custom facts payload).
3. Browse answers and drill into explanations (model/attributes/explanation text).

Here's a brief run-down of the available tools.

### Health check

- `blawx_health`: verifies the Blawx app is reachable and returns status/body.

### Discover Project Content

Agents will usually start by listing the available questions,
fact scenarios, and vocabulary.

- `blawx_questions_list`: lists shared questions available in the project.
- `blawx_question_detail`: retrieves a specific question's details (useful when deciding which question id to ask).
- `blawx_fact_scenarios_list`: lists stored fact scenarios (prebuilt sets of facts you can re-use).
- `blawx_fact_scenario_detail`: shows the facts contained in a specific fact scenario.
- `blawx_ontology_list`: lists ontology categories/relationships (the project's vocabulary).
- `blawx_ontology_category_detail`: details for a specific category.
- `blawx_ontology_relationship_detail`: details for a specific relationship (including arity/parameters).

Additional read-write tools are also available for project editing (questions, fact scenarios, ontology categories/relationships/parameters).

For write operations:

- `blawx_encodingpart_update`, `blawx_question_create`, `blawx_question_update`, `blawx_fact_scenario_create`, and `blawx_fact_scenario_update` all use the same payload shape:

```json
{
	"payload": {
		"blawx_json": {
			"...": "..."
		}
	}
}
```

For question saves specifically, the encoding is expected to include a single outer question block.

- Ontology write tools accept plain JSON objects under `payload`, not `blawx_json` workspaces.
	Current API validation requires these minimum shapes:

```json
{
	"payload": {
		"name": "Contract",
		"slug": "contract",
		"short_description": "",
		"nlg_prefix": "",
		"nlg_postfix": "is a contract"
	}
}
```

```json
{
	"payload": {
		"name": "Estimated Expenditure",
		"slug": "estimated_expenditure",
		"short_description": "",
		"nlg_prefix": ""
	}
}
```

```json
{
	"relationship_id": 458,
	"payload": {
		"order": 1,
		"type_id": 466,
		"nlg_postfix": ""
	}
}
```

Notes:

- Category create/update currently requires `name` and `slug`; `nlg_postfix` must be 50 characters or fewer.
- Relationship create/update currently requires `name` and `slug`.
- Relationship-parameter create/update currently requires `order` and `type_id`.
- Use `blawx_ontology_categories_list` or `blawx_ontology_category_detail` to discover valid category ids for `type_id`.

Patch-style tools are intentionally not exposed in this MCP server to reduce tool-selection ambiguity.

### Ask Questions

- `blawx_question_ask_with_fact_scenario`: asks a question using a stored fact scenario.
- `blawx_question_ask_with_facts`: asks a question using an explicit facts payload generated by your agent based on your
instructions.

Both ask tools currently require shared questions.
If you call either `blawx_question_ask_with_fact_scenario` or
`blawx_question_ask_with_facts` with a non-shared question id, the Blawx app may return
`Question not available via API.` Use a question from `blawx_questions_list`,
or set `shared: true` on the question first.

**NB**: It's not clear how good agents will be at generating
representations of complicated fact scenarios in complicated
vocabularies. It can be helpful to review how your agent
formulated your fact scenario if you get unexpected results,
and to give it hints on how to do better.

When you pose a question, the answer is saved on the Blawx
server for approximately 30 minutes, and your agent can
review it over that period of time. Once the data expires,
your agent will need to pose the question again to analyse
the responses further. Based on the instructions provided
by the MCP server, it should know to do that when and if
required.

### Review Answers

Blawx's answers can be quite large, and agents have a limited
context window, so the process of reviewing
answers is broken into multiple steps.

1. Get the list of answers to the question.
2. Get the list of explanations for a specific answer.
3. Look at the parts of a specific explanation.

- `blawx_list_answers`: gives the list of answers available,
and the bindings in those answers.

- `blawx_cached_response_meta`: metadata (ttl, created, answer_count) for a cached response.

- `blawx_list_explanations`: gives the list of explanations available for an answer

There are four tools to retrieve specific parts of an 
explanation. These tools all allow the agent to select the
entire part, or if it is too long, to select only certain
lines at a time.

- `blawx_get_model_part`: this returns the answer set 
- `blawx_get_attributes_part`: this returns the constraints applied to variables in the model and explanations
- `blawx_get_explanation_part`: this is the tree-structured,
human-readable explanation for the answer
- `blawx_get_constraint_satisfaction_part`: this is the portion
of the explanation that shows how global constraints were satisfied. This is often both verbose and unhelpful, so it
is separated out. You may need to ask your agent to seek it
specifically if you know your encoding uses constraints and
you need to know how they are satisfied.

### Legal Docs + Encoding

The API supports read-write legal documents and parts; for now this MCP server exposes read-only tools for legal docs/parts, and read-write tools for encoding parts.

- `blawx_legaldocs_list`, `blawx_legaldoc_detail`
- `blawx_legaldocparts_list`, `blawx_legaldocpart_detail`
- `blawx_encoding_guide`, `blawx_encodingpart_get`, `blawx_encodingpart_update`, `blawx_encodingpart_delete`

**To read legislation text, use this sequence:**

1. `blawx_legaldocs_list` (or `blawx_legaldoc_detail`) to identify a `legal_doc_id`.
2. `blawx_legaldocparts_list` to list part ids/titles/order for that document.
3. `blawx_legaldocpart_detail` for each relevant `legal_doc_part_id` to retrieve the actual part text/content.

`blawx_legaldocparts_list` is primarily navigational metadata; `blawx_legaldocpart_detail` is the tool that returns the text for a specific part.

**Use this sequence first**:

1. Call `blawx_encoding_guide` (topic `quickstart`, then `encoding-process`, then `encodingpart`, then `blawx-json`).
	Additional available topics include:
	- `valid-blawx-json`: concrete valid payload patterns for `blawx_json`
	- `blawx-blocks`: quick reference of available block types and required components
	- `encoding-process`: step-by-step workflow for creating and updating encoding parts
2. Call `blawx_encodingpart_get` to inspect existing encoding.
3. Call `blawx_encodingpart_update` with payload shape:

```json
{
	"payload": {
		"blawx_json": {
			"...": "..."
		}
	}
}
```

`blawx_encodingpart_update` accepts only **Blawx JSON blocks** via `payload.blawx_json`. Do not send `content`, `scasp_encoding`, or stringified JSON.

**NB**: The other three parts should be read alongside the
attributes, or relevant information may be missing. This
instruction is provided to the agent, but if it isn't followed
your agent may draw incorrect conclusions. It may be wise to
instruct your agent to check the attributes in addition to
the other parts of an explanation.

## Development
The Blawx server used can be overridden for local development

- `BLAWX_BASE_URL` (default: `https://app.blawx.dev`)
