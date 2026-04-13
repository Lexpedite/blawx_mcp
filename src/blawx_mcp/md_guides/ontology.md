# Blawx ontology guidance

Blawx ontologies define two predicate families:

- **Categories**: unary predicates (e.g., `dog/1`), used for typing.
- **Relationships**: predicates with arity 0–10, with typed parameters.

Blawx code can also define symbols, which are called
"objects", by using the object declaration block, which
requires that objects be placed in an initial category.

If you want a unary predicate to represent an ontological
type, use a category. If you want a unary predicate to
represent a binary property of an entity, use a unary
relationship. If you want to deal with identity, use
objects.

## Rules

- Parameters are typed using categories or supported datatypes (numbers, dates, datetimes, times, durations).
- When encoding, only use the ontology’s predicates, Undefined predicates will fail.
- Negative versions of predicates are not required in the ontology
- NLG components (i.e. prefix, postfix, postfixN) are required.
- in relationships, prefix appears before the first parameter (if any), postfixN appears after the Nth parameter (1-index)
- for categories, the object is the only parameter, and postfix appears after it.
- Example: "employee(X)" -> prefix "", postfix "is an employee"
- Example: "works_for(X,Y)" -> prefix "", postfix1 "works for", postfix2 ""

## MCP ontology write payloads

The ontology write tools do not accept `blawx_json` workspaces. They accept
plain JSON objects as `payload`.

### Category create/update

Current API validation requires `name` and `slug`.

Common payload shape:

```json
{
	"name": "Contract",
	"slug": "contract",
	"short_description": "",
	"nlg_prefix": "",
	"nlg_postfix": "is a contract"
}
```

Notes:

- `nlg_postfix` is limited to 50 characters by the current API.
- Category read responses may also include `long_description`.

### Relationship create/update

Current API validation requires `name` and `slug`.

Common payload shape:

```json
{
	"name": "Estimated Expenditure",
	"slug": "estimated_expenditure",
	"short_description": "",
	"nlg_prefix": ""
}
```

### Relationship parameter create/update

Current API validation requires `order` and `type_id`.

Common payload shape:

```json
{
	"order": 1,
	"type_id": 466,
	"nlg_postfix": ""
}
```

Notes:

- `type_id` must be the id of an ontology category.
- Use `blawx_ontology_categories_list` or `blawx_ontology_category_detail` to find valid category ids.
- `blawx_ontology_relationship_parameters_list` shows the `type_slug` currently associated with each parameter.
