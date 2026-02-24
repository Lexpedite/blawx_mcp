# Blawx ontology guidance

Blawx ontologies define two predicate families:

- **Categories**: unary predicates (e.g., `dog/1`), used for typing.
- **Relationships**: predicates with arity 0–10, with typed parameters.

## Rules

- Parameters are typed using categories or supported datatypes (numbers, dates, datetimes, times, durations).
- When encoding, only use the ontology’s predicates, Undefined predicates will fail.
- Negative versions of predicates are not required in the ontology
- NLG components (i.e. prefix, postfix, postfixN) are required.
- in relationships, prefix appears before the first parameter (if any), postfixN appears after the Nth parameter (1-index)
- for categories, the object is the only parameter, and postfix appears after it.
- Example: "employee(X)" -> prefix "", postfix "is an employee"
- Example: "works_for(X,Y)" -> prefix "", postfix1 "works for", postfix2 ""
