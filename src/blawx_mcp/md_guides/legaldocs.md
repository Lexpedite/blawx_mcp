# LegalDocs and LegalDocParts in Blawx

Use this guide when you need to navigate or edit the legal text structure that sits above encoding parts.

## Team and project selection first

All legal-document tools are project-scoped.

1. Call `blawx_teams_list`.
2. If exactly one team is returned, use that team's `slug` as `team_slug`; if multiple teams are returned and the user has not identified one, ask which team to use.
3. Call `blawx_projects_list` with `team_slug`.
4. Choose the target `project_id`.
5. Pass that `team_slug` and `project_id` to every legal-doc, part, ontology, question, fact-scenario, and encoding-part tool.

Only `blawx_health`, `blawx_teams_list`, and `blawx_encoding_guide` can be used before project selection.

## Resource model

- A LegalDoc is a top-level source document such as an act, regulation, or policy.
- A LegalDocPart is a structural segment within a LegalDoc.
- An EncodingPart attaches reasoning blocks to a specific LegalDocPart.

Because one EncodingPart attaches to one LegalDocPart, plan the LegalDocPart hierarchy before you begin encoding.

Typical navigation flow:

1. `blawx_legaldocs_list`
2. `blawx_legaldoc_detail`
3. `blawx_legaldocparts_list`
4. `blawx_legaldocpart_detail`
5. `blawx_encodingpart_get` or `blawx_encodingpart_update`

## Default LegalDocPart granularity rule

Preserve the legislative hierarchy by default. Do not bundle multiple separately addressable
legislative units into one LegalDocPart when those units should appear separately in the source structure.

Use this default splitting model:

- Each heading gets its own LegalDocPart when the heading text appears as a distinct unit.
- Each section gets its own LegalDocPart for the section text that appears before subordinate units.
- A section with no subordinate units is a single LegalDocPart.
- Each subsection, paragraph, subparagraph, clause, item, or similar subordinate unit gets its own LegalDocPart when it has distinct text in the legislative hierarchy.
- Keep units separate even when their logic is closely related. Link the logic in encoding rules instead of merging the source text into one part.

Explicit exception:

- If the source does not actually split the text into separately addressable subordinate units, keep it as one LegalDocPart for that single textual unit.

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
- `element_type` (optional; e.g. "section" or "paragraph"; used alongside index text to generate pinpoints)
- `index_text` (optional; e.g. "1.", "(a)"; used to generate pinpoints)
- `text_content` (optional; the actual text content of the section of the legal document, which may be a heading)
- `include_parent` (optional; whether the current part must be read in the context of its parent, and not just on its own, to be read clearly)
- `include_sibling` (optional; whether the current part must be read in the context of its immediately prior sibling, and not just its parent, to be read clearly)
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

## How hierarchy and context fields fit the model

- `parent_id` defines where a new LegalDocPart sits in the legislative hierarchy. Use it to create the heading -> section -> subsection -> paragraph tree.
- `include_parent=true` when a part cannot be understood without reading its parent part's text as context.
- `include_sibling=true` when a part must be read together with its immediately preceding sibling text for clarity.
- These flags provide reading context. They do not justify merging separate legislative units into one LegalDocPart.
- If two units should be cited or encoded separately, create separate parts and connect them through hierarchy and encoding logic.

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

## Worked structure examples

### Example 1: Heading -> section -> subsection -> paragraph

Source structure:

1. Heading: `Part II Licensing`
2. Section 7 opening text: `A person may apply for a licence if the person meets the following conditions.`
3. Subsection 7(1): `The applicant must be an adult.`
4. Paragraph 7(1)(a): `The applicant must reside in the province.`

Recommended LegalDocParts:

1. Heading part for `Part II Licensing`
2. Section part for the opening text of section 7 only
3. Subsection part for section 7(1)
4. Paragraph part for section 7(1)(a)

Relationships:

- Create the heading part first.
- Create the section part with that heading's id as `parent_id` if your source hierarchy places the section under the heading.
- Create the subsection part with the section part's id as `parent_id`.
- Create the paragraph part with the subsection part's id as `parent_id`.
- Set `include_parent` or `include_sibling` only when the text needs that surrounding context to read clearly.

Do not combine the heading, section opening text, subsection text, and paragraph text into one LegalDocPart. They are separate hierarchical units and should remain separately addressable.

### Example 2: Standalone section with no subordinate units

Source structure:

1. Section 12: `A licence expires one year after the day on which it is issued.`

Recommended LegalDocParts:

1. One section part for section 12.

Because there are no subordinate units with distinct text, one LegalDocPart is the correct structure for that section.

For the full encoding workflow, return to guide topic: `encoding-process`.
