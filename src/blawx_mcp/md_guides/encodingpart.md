# EncodingParts in Blawx

An EncodingPart represents the code encoding of a specific legal-text segment.

This guide is intentionally narrow: it defines tool behavior and write-contract constraints.

For the full end-to-end authoring workflow, use `encoding-process` first.

## Mandatory first step

Before any project-scoped tool call, call `blawx_projects_list`, choose the target
`project_id`, and pass that `project_id` to every later legal-doc, ontology, question,
fact-scenario, ask/answer, and encoding tool call.

Only `blawx_health` and `blawx_encoding_guide` can be used before project selection.

Plan LegalDocPart structure before encoding. One EncodingPart attaches to one LegalDocPart,
so if the legislation should be split into multiple parts, create those parts first and then
encode them separately.

## Tool touchpoints

- `blawx_encodingpart_get`: read the current encoding for a legal doc part.
- `blawx_encodingpart_update`: replace encoding using `blawx_json` payload.
- `blawx_encodingpart_delete`: remove existing encoding for a legal doc part.
- Legal text navigation/write tools: `blawx_legaldocs_list`, `blawx_legaldocparts_list`, `blawx_legaldocpart_detail`, `blawx_legaldoc_create`, `blawx_legaldoc_update`, `blawx_legaldoc_delete`, `blawx_legaldocpart_create`, `blawx_legaldocpart_update`, `blawx_legaldocpart_delete`.

Important: `blawx_legaldocparts_list` is primarily navigational metadata (ids/titles/order).
Use `blawx_legaldocpart_detail` to read the text of a specific legal doc part.

## Important: what the write tools accept

The MCP write tools for encoding parts intentionally accept **only the Blawx JSON blocks** encoding.

- Provide the JSON blocks structure (as JSON, not a string).
- Do **not** provide s(CASP) text/code in the write tools.
- Blawx should (re)calculate the s(CASP) encoding automatically when the JSON changes.

Legal document structure, LegalDocPart granularity, and write-field guidance now live in guide topic: `legaldocs`.
