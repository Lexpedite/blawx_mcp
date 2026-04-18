# Blawx Encoding Process (Primary Workflow)

This is the primary workflow guide for building or revising encoding parts.

Use this guide first, then follow the referenced specialized guides at each step.

## Tool touchpoints

- Project discovery: `blawx_projects_list`
- Legal text discovery: `blawx_legaldocs_list`, `blawx_legaldocparts_list`, `blawx_legaldocpart_detail`
- Existing encoding: `blawx_encodingpart_get`
- Ontology inspection/update: `blawx_ontology_list`, `blawx_ontology_category_detail`, `blawx_ontology_relationship_detail`, and related ontology write tools if needed
- Test setup: `blawx_questions_list`, `blawx_question_detail`, fact-scenario tools, and related write tools if needed
- Test execution and analysis: ask tools, `blawx_list_answers`, explanation-part tools
- Encoding write: `blawx_encodingpart_update`

## 1) Select the project first

1. Call `blawx_projects_list` and choose the `project_id` you will pass to every project-scoped tool.
2. Treat that `project_id` as mandatory for all later ontology, legal-doc, question, fact-scenario, ask/answer, and encoding calls.
3. Only `blawx_health` and `blawx_encoding_guide` can be used without that `project_id`.

## 2) Select source sections

1. Identify the legal document and relevant parts.
2. Read the text of each target part in context.
3. Skip non-substantive or administrative sections unless they affect reasoning outcomes.

If needed for project/legal-document navigation and write behavior, read guide topics: `legaldocs` and `encodingpart`.

## 3) Plan traceable rule boundaries

Choose whether to encode complete sections or partial sentence structures for better explanation traceability.

Use this LegalDocPart decision framework before you write blocks:

1. Preserve the legislative hierarchy by default. Do not bundle multiple separately addressable legislative units into one LegalDocPart just because the logic is related.
2. Give each heading its own LegalDocPart when the heading text appears as a distinct unit in the source.
3. Give each section its own LegalDocPart for the section-level text that appears before any subordinate units.
4. If a section has no subordinate units, one LegalDocPart for that section is sufficient.
5. Give each subsection, paragraph, subparagraph, clause, item, or similar subordinate unit its own LegalDocPart when it has distinct text in the legislative hierarchy.
6. If a subordinate unit depends on a heading or introductory text for readability, keep separate parts and use hierarchy plus context fields instead of merging the text into one part.
7. Use separate encoding rules to connect shared logic across parts. Do not merge source units into one part to avoid writing multiple rules.

Useful pattern:

1. Predicate is true when:
   a. Sub-rule A is satisfied, or
   b. Sub-rule B is satisfied.

Model this as a parent rule that concludes the predicate when either child sub-rule holds.

Worked examples:

1. Heading -> section -> subsection -> paragraph.
  Create one part for the heading text, one part for the section's opening text, one part for each subsection text, and one part for each paragraph text nested under its subsection.
2. Standalone section with no subsections.
  Create one part for the section text and encode that part directly.

## 4) Choose implementation order

Encode sections in an order that minimizes rework:

- Start with rules whose conclusions are not heavily dependent on rules that have not yet been encoded.
- Delay sections whose conditions rely on conclusions that are still missing.

## 5) Design target logic before writing blocks

For each section:

1. Write pseudocode for facts, conditions, conclusions, and exceptions.
2. Confirm ontology support for every category/relationship needed.
3. If ontology changes are required, apply them before encoding the section.

For ontology-specific design rules and NLG constraints, read guide topic: `ontology`.

## 6) Prepare tests before finalizing encoding

Create or select fact scenarios and questions that can verify both positive and negative behavior.

When creating/updating test assets with MCP write tools:

- `blawx_question_create`, `blawx_question_update`, `blawx_fact_scenario_create`, and `blawx_fact_scenario_update` require all of:
  - `name`
  - `slug`
  - `blawx_json`
- Questions also support `shared` (boolean). Set `shared=true` when you intend to discover/use the question via shared-question read tools.
- If a question is non-shared, use `blawx_questions_list_all` / `blawx_question_detail_all` instead of shared-question tools.
- `blawx_encodingpart_update` is different and accepts only `blawx_json`.

- Include tests for expected conclusions.
- Include tests for expected failure cases where appropriate.
- Consider whether negation-as-failure behavior needs explicit test cases.

## 7) Build or revise the encoding JSON

Generate the `blawx_json` blocks that implement the target logic.

- Prefer explicit category-membership checks early in rule conditions.
- Use block structures consistent with ontology arity/parameter typing.

For block-shape and syntax rules, read guide topics: `blawx-json` and `blawx-blocks`.

For concrete valid payload examples, read guide topics: `valid-blawx-json` and `encoding-examples`.

## 8) Write encoding using the MCP contract

1. Read current encoding using `blawx_encodingpart_get`.
2. Write with `blawx_encodingpart_update` using only:

```json
{
  "blawx_json": { ... }
}
```

For strict write-contract details, read guide topic: `encodingpart`.

Remember: every tool in this workflow other than `blawx_health` and `blawx_encoding_guide`
now requires the explicit `project_id` you selected at the start.

## 9) Execute tests and inspect explanations

Run selected questions against selected fact scenarios, then inspect answers and explanations.

- If behavior is wrong, determine whether the issue is in ontology, scenarios, questions, or encoding blocks.
- If explanation wording is strange, check ontology NLG components and relationship usage consistency.

Revise and repeat until outcomes and explanations are both acceptable.

## 10) Move to next section and iterate

When a section passes tests, continue to the next section according to the planned order.