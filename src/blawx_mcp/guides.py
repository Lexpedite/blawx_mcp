"""Human guidance exposed via MCP resources/prompts.

These are intentionally written as standalone markdown snippets so that:
- agents that support MCP resources can fetch and read them, and
- agents that only use tool descriptions still get the essentials via tool docstrings.
"""

from pathlib import Path


def _read_md_guide(filename: str) -> str:
   path = Path(__file__).resolve().parent / "md_guides" / filename
   try:
      return path.read_text(encoding="utf-8")
   except FileNotFoundError:
      return f"# Missing guide\n\nCould not find `{filename}` in `md_guides`."

SCA_SP_GUIDE_MD = """# s(CASP) encoding guidance (Blawx)

## Core modeling constraints

- No disjunction operator. Represent disjunctions as multiple rules with the same conclusion.
- Two kinds of negation:
  - Explicit/strong negation: `-pred(...)` (concretely known false)
  - Negation as failure: `not pred(...)` or `not -pred(...)`
- Rules must have exactly one conclusion.
- The conclusion of a rule cannot use negation as failure (`not`).
- Prefer checking category membership before other relationships (efficiency + clarity).
- Inequality uses `\\=`.

## Ontology discipline

- Only use predicates defined by the project ontology (and their explicitly-negated duals).
- Do not invent new predicate names in the encoding.
- If something is missing, *recommend* an ontology addition separately rather than using it in code.

## Suggested workflow (structured output)

1. List logical facts and implications from the target text.
2. List ontology elements used (categories + relationships).
3. For each concept that does not map well, propose a category/relationship to add.
4. Draft pseudocode:
   - Facts: “we know {statement}”
   - Rules: “we know {conclusion} when we know {conditions}”
5. Produce s(CASP) code that follows the constraints above.
"""

ONTOLOGY_GUIDE_MD = """# Blawx ontology guidance

Blawx ontologies define two predicate families:

- **Categories**: unary predicates (e.g., `dog/1`), used for typing.
- **Relationships**: predicates with arity 0–10, with typed parameters.

## Rules

- Parameters are typed using categories or supported datatypes (numbers, dates, datetimes, times, durations).
- When encoding, only use the ontology’s predicates (and their explicit negations, `-pred(...)`).
- You may use negation as failure (`not`).
- If the ontology does not contain a needed concept, recommend an addition rather than inventing predicates.
"""

BLAWX_JSON_GUIDE_MD = """# Blawx JSON (visual blocks) encoding guidance

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

## Suggested workflow (structured output)

1. List logical facts and implications.
2. Draft natural-language pseudocode using the ontology terms.
3. Produce valid Blawx JSON blocks (not a string) that match the selected block types.
"""

ENCODINGPART_GUIDE_MD = """# EncodingParts in Blawx

An EncodingPart represents the code encoding of a specific legal-text segment.

Typical agent flow:

1. Fetch legal docs with `blawx_legaldocs_list` and pick the target `legal_doc_id`.
2. Fetch parts via `blawx_legaldocparts_list`.
3. Fetch the actual legal text/content for each relevant part with `blawx_legaldocpart_detail`.
4. Fetch ontology + examples if available.
5. Generate a suggested encoding (s(CASP) or Blawx JSON) following the guides.
6. Write back via the encoding tools:
   - `blawx_encodingpart_update` (PUT)
   - `blawx_encodingpart_patch` (PATCH)

Important: `blawx_legaldocparts_list` is primarily navigational metadata (ids/titles/order).
Use `blawx_legaldocpart_detail` to read the text of a specific legal doc part.

## Important: what the write tools accept

The MCP write tools for encoding parts intentionally accept **only the Blawx JSON blocks** encoding.

- Provide the JSON blocks structure (as JSON, not a string).
- Do **not** provide s(CASP) text/code in the write tools.
- Blawx should (re)calculate the s(CASP) encoding automatically when the JSON changes.

This MCP server intentionally does **not** expose tools to create/update legal docs or legal doc parts yet.
"""


BLAWX_BLOCKS_GUIDE_MD = _read_md_guide("blawx_blocks.md")
VALID_BLAWX_JSON_GUIDE_MD = _read_md_guide("valid_blawx_json.md")
