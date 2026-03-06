# Blawx JSON (visual blocks) encoding guidance

Blawx’s visual language serializes into a JSON structure of blocks.

This guide covers JSON/block structure only.

For end-to-end section selection, ontology planning, testing flow, and iteration process, use `encoding-process`.

## Tool touchpoints

- Read/write encoding parts: `blawx_encodingpart_get`, `blawx_encodingpart_update`
- Reference material: `blawx_encoding_guide` topics `blawx-blocks`, `valid-blawx-json`, `encoding-examples`

## Block JSON shape

Blocks can include: `type`, `inputs`, `fields`, `extraState`, and (for statement blocks) `next`.

- Only `type` is universally required, but **this server’s prompt guidance assumes required inputs/fields are present**.
- Statement blocks can be stacked using `next` (conjunction).
- Value blocks do not have `next`.

## Key constraints

- No disjunction operator: represent disjunctions as multiple rules with the same conclusion.
- Variable names must be capitalized (e.g., `A`).
- Object names must be lowercase atoms (e.g., `john_doe`).
- Prefer category-membership tests early in rule conditions when possible.
- Prefer brief but semantically meaningful variable names ("Person" over "X")

Examples of encodings are available in `encoding-examples` and validation-oriented examples are in `valid-blawx-json`.