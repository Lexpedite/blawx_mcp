# LegalDocs and LegalDocParts in Blawx

Use this guide when you need to navigate or edit the legal text structure that sits above encoding parts.

## Project selection first

All legal-document tools are project-scoped.

1. Call `blawx_projects_list`.
2. Choose the target `project_id`.
3. Pass that `project_id` to every legal-doc, part, ontology, question, fact-scenario, and encoding-part tool.

## Resource model

- A LegalDoc is a top-level source document such as an act, regulation, or policy.
- A LegalDocPart is a structural segment within a LegalDoc.
- An EncodingPart attaches reasoning blocks to a specific LegalDocPart.

Typical navigation flow:

1. `blawx_legaldocs_list`
2. `blawx_legaldoc_detail`
3. `blawx_legaldocparts_list`
4. `blawx_legaldocpart_detail`
5. `blawx_encodingpart_get` or `blawx_encodingpart_update`

## What list tools return

- `blawx_legaldocs_list` returns document metadata, not the legal text.
- `blawx_legaldocparts_list` returns navigational metadata such as `id`, `parent_id`, `path`, `depth`, `element_type`, and `index_text`.
- `blawx_legaldocpart_detail` returns the actual part content and context fields.

## LegalDoc write contract

LegalDoc create and update calls use these fields:

- `name` (required)
- `slug` (required)
- `tag_ids` (optional, defaults to `[]`)

Observed response shape:

```json
{
  "id": 84,
  "name": "MCP Temp LegalDoc",
  "slug": "mcp-temp-legaldoc",
  "tag_ids": []
}
```

`blawx_legaldoc_delete` removes the document at the specified id.

## LegalDocPart write contract

LegalDocPart creation is tied to the LegalDoc in the URL.
The server populates `legal_doc_id`, `path`, `depth`, `numchild`, `content_in_context`, and `pincite`.

Fields accepted on create:

- `parent_id` (optional; use only at creation time when nesting under an existing part)
- `element_type` (optional; e.g. "section" or "paragraph"; used alonside index text to generate pinpoints)
- `index_text` (optional; e.g. "1.", "(a)"; used to generate pinpoints)
- `text_content` (optional; the actual text content of the section of the legal document, which may be a heading)
- `include_parent` (optional; whether the curent section must be read in the context of its parent (and not prior siblings) to be read clearly)
- `include_sibling` (optional; whether the current section must be read in the context of its immediately prior parent (and not its parent) to be read clearly)
- `substantive` (optional; indicates whether the section has legal effect, or is a navigational aid, like a header)

An empty create payload is valid; the server will create a default top-level part.

Fields accepted on update:

- `element_type`
- `index_text`
- `text_content`
- `include_parent`
- `include_sibling`
- `substantive`

Important: do not include `parent_id` in update payloads. The current API rejects re-parenting via PUT, even when the value is unchanged.

Observed part response shape:

```json
{
  "id": 649,
  "legal_doc_id": 85,
  "parent_id": null,
  "path": "003I",
  "depth": 1,
  "numchild": 0,
  "element_type": "Subsection",
  "index_text": "(1)",
  "text_content": "After update.",
  "include_parent": false,
  "include_sibling": false,
  "substantive": true,
  "content_in_context": "[After update.]\n",
  "pincite": "MCP-TEMP-UPDATE-TEST Subsection (1)"
}
```

## Relationship to encoding parts

- Use LegalDoc and LegalDocPart tools to manage the source-text hierarchy.
- Use EncodingPart tools to manage the logical encoding attached to one LegalDocPart.
- If you create a new LegalDocPart that needs reasoning, the usual next step is `blawx_encodingpart_update`.

For the full encoding workflow, return to guide topic: `encoding-process`.
