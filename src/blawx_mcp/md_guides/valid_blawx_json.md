# EncodingPart valid `blawx_json` payload examples

This document gives example payloads for the EncodingPart MCP tools.

For the full authoring/testing loop, use `encoding-process` first.

## Tool touchpoints

- `blawx_encodingpart_get`: inspect current content before replacing
- `blawx_encodingpart_update`: submit payload with `blawx_json`

## Payload contract for EncodingPart write tools

Use this shape:

```json
{
  "blawx_json": { ... }
}
```

### Required validation rules

`blawx_json` must be:
- a JSON object, or
- a JSON string that parses to an object (still accepted by the current Blawx app)

And for non-empty workspaces (`blawx_json != {}`), it must satisfy:
- Blockly workspace shape:
  - `blocks` object exists
  - `blocks.languageVersion` is an integer
  - `blocks.blocks` is a list
- block types are known/supported
- ontology/object references are valid for the target project
- block types forbidden for encoding parts are not used
- `doc_selector` blocks require `extraState.section_reference`
- use `object_declaration` to create new objects and supply `extraState.category_name`
- `object_category` blocks use `fields.category_name` and `inputs.object`
- declared object names should not end in an underscore followed by digits, such as `contract_1`

In MCP usage, this object is provided as the `payload` argument to
`blawx_encodingpart_update`.

---

## Example 1: fully empty workspace (valid)

```json
{
  "blawx_json": {}
}
```

Notes:
- This is explicitly accepted.
- Blawx stores empty generated content (`"content": ""`).

---

## Example 2: minimal Blockly workspace with no top-level blocks (valid)

```json
{
  "blawx_json": {
    "blocks": {
      "languageVersion": 0,
      "blocks": []
    }
  }
}
```

Notes:
- This satisfies structural workspace validation.
- This shape is accepted by EncodingPart write tool validation.

---

## Example 3: JSON-string form (currently valid)

```json
{
  "blawx_json": "{\"blocks\":{\"languageVersion\":0,\"blocks\":[]}}"
}
```

Notes:
- Current normalization in Blawx accepts a JSON string and parses it.
- Prefer object form in new clients for clarity.

---

## Example 4: non-empty workspace with ontology-aware blocks (conditionally valid)

This is valid **only if**:
- category `person` exists in the target project ontology, and
- relationship `employed_by` exists and has arity 2.

```json
{
  "blawx_json": {
    "blocks": {
      "languageVersion": 0,
      "blocks": [
        {
          "type": "object_declaration",
          "fields": {
            "object_name": "alice",
            "prefix": "",
            "postfix": ""
          },
          "extraState": {
            "category_name": "person"
          }
        },
        {
          "type": "relationship_selector",
          "extraState": {
            "relationship_name": "employed_by",
            "arity": 2
          },
          "inputs": {
            "first_element": {
              "block": {
                "type": "object_selector",
                "fields": { "object_name": "alice" }
              }
            },
            "second_element": {
              "block": {
                "type": "variable",
                "fields": { "variable_name": "Employer" }
              }
            }
          }
        }
      ]
    }
  }
}
```