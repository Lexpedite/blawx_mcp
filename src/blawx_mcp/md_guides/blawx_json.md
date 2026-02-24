# Blawx JSON (visual blocks) encoding guidance

Blawx’s visual language serializes into a JSON structure of blocks.

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

## Suggested workflow (structured output)

1. List logical facts and implications.
2. Draft natural-language pseudocode using the ontology terms.
3. Produce valid Blawx JSON blocks (not a string) that match the selected block types.

Examples of encodings are available in another guide.