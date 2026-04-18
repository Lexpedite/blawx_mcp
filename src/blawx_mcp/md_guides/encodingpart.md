# EncodingParts in Blawx

An EncodingPart represents the code encoding of a specific legal-text segment.

This guide is intentionally narrow: it defines tool behavior and write-contract constraints.

For the full end-to-end authoring workflow, use `encoding-process` first.

## Tool touchpoints

- `blawx_encodingpart_get`: read the current encoding for a legal doc part.
- `blawx_encodingpart_update`: replace encoding using `blawx_json` payload.
- `blawx_encodingpart_delete`: remove existing encoding for a legal doc part.
- Legal text navigation/write tools: `blawx_legaldocs_list`, `blawx_legaldocparts_list`, `blawx_legaldocpart_detail`, `blawx_legaldoc_create`, `blawx_legaldoc_update`, `blawx_legaldoc_delete`, `blawx_legaldocpart_create`, `blawx_legaldocpart_update`, `blawx_legaldocpart_delete`.

Important: `blawx_legaldocparts_list` is primarily navigational metadata (ids/titles/order).
Use `blawx_legaldocpart_detail` to read the text of a specific legal doc part.

Before any of those tools, select a project with `blawx_projects_list` and pass that
`project_id` through every project-scoped call.

## Important: what the write tools accept

The MCP write tools for encoding parts intentionally accept **only the Blawx JSON blocks** encoding.

- Provide the JSON blocks structure (as JSON, not a string).
- Do **not** provide s(CASP) text/code in the write tools.
- Blawx should (re)calculate the s(CASP) encoding automatically when the JSON changes.

Legal document structure and write-field guidance now lives in guide topic: `legaldocs`.
