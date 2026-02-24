# s(CASP) encoding guidance (Blawx)

## Core modeling constraints

- No disjunction operator. Represent disjunctions as multiple rules with the same conclusion.
- Two kinds of negation:
  - Explicit/strong negation: `-pred(...)` (concretely known false)
  - Negation as failure: `not pred(...)` or `not -pred(...)`
- Rules must have exactly one conclusion.
- The conclusion of a rule cannot use negation as failure (`not`).
- Prefer checking category membership before other relationships (efficiency + clarity).
- Inequality uses `\=`.

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
