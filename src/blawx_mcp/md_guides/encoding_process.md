# Blawx Encoding Process (Primary Workflow)

This is the primary workflow guide for building or revising encoding parts.

Use this guide first, then follow the referenced specialized guides at each step.

## Tool touchpoints

- Legal text discovery: `blawx_legaldocs_list`, `blawx_legaldocparts_list`, `blawx_legaldocpart_detail`
- Existing encoding: `blawx_encodingpart_get`
- Ontology inspection/update: `blawx_ontology_list`, `blawx_ontology_category_detail`, `blawx_ontology_relationship_detail`, and related ontology write tools if needed
- Test setup: `blawx_questions_list`, `blawx_question_detail`, fact-scenario tools, and related write tools if needed
- Test execution and analysis: ask tools, `blawx_list_answers`, explanation-part tools
- Encoding write: `blawx_encodingpart_update`

## 1) Select source sections

1. Identify the legal document and relevant parts.
2. Read the text of each target part in context.
3. Skip non-substantive or administrative sections unless they affect reasoning outcomes.

If needed for tool behavior and legal-doc navigation details, read guide topic: `encodingpart`.

## 2) Plan traceable rule boundaries

Choose whether to encode complete sections or partial sentence structures for better explanation traceability.

Useful pattern:

1. Predicate is true when:
   a. Sub-rule A is satisfied, or
   b. Sub-rule B is satisfied.

Model this as a parent rule that concludes the predicate when either child sub-rule holds.

## 3) Choose implementation order

Encode sections in an order that minimizes rework:

- Start with rules whose conclusions are not heavily dependent on rules that have not yet been encoded.
- Delay sections whose conditions rely on conclusions that are still missing.

## 4) Design target logic before writing blocks

For each section:

1. Write pseudocode for facts, conditions, conclusions, and exceptions.
2. Confirm ontology support for every category/relationship needed.
3. If ontology changes are required, apply them before encoding the section.

For ontology-specific design rules and NLG constraints, read guide topic: `ontology`.

## 5) Prepare tests before finalizing encoding

Create or select fact scenarios and questions that can verify both positive and negative behavior.

- Include tests for expected conclusions.
- Include tests for expected failure cases where appropriate.
- Consider whether negation-as-failure behavior needs explicit test cases.

## 6) Build or revise the encoding JSON

Generate the `blawx_json` blocks that implement the target logic.

- Prefer explicit category-membership checks early in rule conditions.
- Use block structures consistent with ontology arity/parameter typing.

For block-shape and syntax rules, read guide topics: `blawx-json` and `blawx-blocks`.

For concrete valid payload examples, read guide topics: `valid-blawx-json` and `encoding-examples`.

## 7) Write encoding using the MCP contract

1. Read current encoding using `blawx_encodingpart_get`.
2. Write with `blawx_encodingpart_update` using only:

```json
{
  "blawx_json": { ... }
}
```

For strict write-contract details, read guide topic: `encodingpart`.

## 8) Execute tests and inspect explanations

Run selected questions against selected fact scenarios, then inspect answers and explanations.

- If behavior is wrong, determine whether the issue is in ontology, scenarios, questions, or encoding blocks.
- If explanation wording is strange, check ontology NLG components and relationship usage consistency.

Revise and repeat until outcomes and explanations are both acceptable.

## 9) Move to next section and iterate

When a section passes tests, continue to the next section according to the planned order.