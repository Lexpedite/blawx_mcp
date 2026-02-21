# Blawx blocks quick reference (available blocks + required components)

## How to read "required components"

For block instances in `blawx_json`:
- named `field_*` args become required entries in `fields.<name>`
- named `input_*` args become required entries in `inputs.<name>`
- some blocks also require `extraState` keys (notably ontology/relationship blocks)

If a block has no named args, required components are shown as `none`.

---

## Core logic and reasoning blocks

- `variable`: fields `variable_name`
- `silent_variable`: fields `variable_name`
- `unnamed_variable`: none
- `variable_assignment`: inputs `variable`, `value`
- `conjunction`: inputs `conjoined_statements`
- `logical_negation`: inputs `negated_statement`
- `default_negation`: inputs `default_negated_statement`
- `comparison`: fields `operator`; inputs `first_comparator`, `second_comparator`
- `fact`: inputs `source`, `statements`
- `query`: inputs `query`
- `rule`: inputs `source`, `conditions`, `conclusion`
- `unattributed_rule`: inputs `conditions`, `conclusion`
- `unattributed_fact`: inputs `statements`
- `constraint`: inputs `source`, `conditions`
- `unattributed_constraint`: inputs `conditions`
- `assume`: inputs `statements`
- `according_to`: inputs `rule`, `statement`
- `overrules`: inputs `defeating_rule`, `defeating_statement`, `defeated_rule`, `defeated_statement`
- `opposes`: inputs `first_statement`, `second_statement`
- `defeated`: inputs `defeating_rule`, `defeating_statement`
- `applies`: inputs `applicable_rule`, `object`
- `attributed_fact`: fields `exceptions`; inputs `source`, `statement`
- `attributed_rule`: fields `defeasible`, `inapplicable`; inputs `conditions`, `source`, `conclusion`


---

## Document Selector and reference blocks

- `doc_selector`: fields `doc_part_name`
- `holds`: inputs `section`, `statement`

---

## Ontology and object/category blocks

- `category_equivalence`: inputs `first_category`, `second_category`
- `object_selector`: fields `object_name`
- `object_declaration`: fields `prefix`, `object_name`, `postfix`; extraState `category_name`
- `new_object_category`: fields `category_name`; inputs `object`
- `object_category`: inputs `object`, `category`
- `object_equality`: inputs `first_object`, `second_object`
- `object_disequality`: inputs `first_object`, `second_object`

---

## Relationship blocks

- `relationship_selector`: fields `prefix1`, `prefix2`, `prefix3`, `postfix`; inputs `first_element`, `second_element`, `third_element`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector3`: fields `prefix1`, `prefix2`, `prefix3`, `postfix`; inputs `parameter1`, `parameter2`, `parameter3`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector4`: fields `prefix1`..`prefix4`, `postfix`; inputs `parameter1`..`parameter4`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector5`: fields `prefix1`..`prefix5`, `postfix`; inputs `parameter1`..`parameter5`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector6`: fields `prefix1`..`prefix6`, `postfix`; inputs `parameter1`..`parameter6`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector7`: fields `prefix1`..`prefix7`, `postfix`; inputs `parameter1`..`parameter7`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector8`: fields `prefix1`..`prefix8`, `postfix`; inputs `parameter1`..`parameter8`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector9`: fields `prefix1`..`prefix9`, `postfix`; inputs `parameter1`..`parameter9`; extraState `relationship_name` (and optional `arity`)
- `relationship_selector10`: fields `prefix1`..`prefix10`, `postfix`; inputs `parameter1`..`parameter10`; extraState `relationship_name` (and optional `arity`)

---

## Primitive value blocks

- `number_value`: fields `value`
- `date_value`: fields `year`, `month`, `day`
- `duration_value`: fields `sign`, `days`, `hours`, `minutes`, `seconds`
- `time_value`: fields `hours`, `minutes`, `seconds`
- `datetime_value`: fields `year`, `month`, `day`, `hours`, `minutes`, `seconds`

---

## Math/date/time/duration operations

- `calculation`: inputs `variable`, `calculation`
- `math_operation`: fields `operator`; inputs `left_side`, `right_side`
- `numerical_constraint`: fields `operator`; inputs `first_comparator`, `second_comparator`
- `date_comparison`: fields `comparison`; inputs `first_date`, `second_date`
- `date_element`: fields `element`; inputs `date`
- `date_calculate`: inputs `year`, `month`, `day`
- `duration_calculate`: inputs `sign`, `years`, `months`, `days`, `hours`, `minutes`, `seconds`
- `duration_element`: fields `element`; inputs `duration`
- `date_difference_days`: inputs `first_date`, `second_date`, `duration_days`
- `date_difference`: inputs `first_date`, `second_date`, `duration`
- `date_add`: inputs `duration`, `first_date`, `second_date`
- `date_add_days`: inputs `days`, `first_date`, `second_date`
- `duration_comparison`: fields `comparison`; inputs `first_date`, `second_date`
- `time_comparison`: fields `comparison`; inputs `first_time`, `second_time`
- `time_calculate`: inputs `hours`, `minutes`, `seconds`
- `datetime_calculate`: inputs `year`, `month`, `day`, `hours`, `minutes`, `seconds`
- `datetime_construct`: inputs `date`, `time`, `datetime`
- `now`: inputs `now`
- `today`: inputs `NAME`

---

## Timestamp conversion blocks

- `datetime_to_ts`: inputs `datetime`, `timestamp`
- `ts_to_datetime`: inputs `timestamp`, `datetime`
- `datetime_ts`: inputs `datetime`, `timestamp`
- `time_from_ts`: inputs `timestamp`
- `datetime_from_ts`: inputs `timestamp`
- `date_from_ts`: inputs `timestamp`
- `duration_from_ts`: inputs `timestamp`

---

## Event calculus / temporal reasoning blocks

- `happens`: inputs `time`, `event`
- `initiates`: inputs `time`, `statement`
- `terminates`: inputs `time`, `statement`
- `holds_at`: inputs `time`, `statement`
- `initially`: inputs `statement`
- `trajectory`: inputs `initial_time`, `initial_fluent`, `subsequent_time`, `subsequent_fluent`
- `started_in`: inputs `start_time`, `end_time`, `statement`
- `stopped_in`: inputs `start_time`, `end_time`, `statement`
- `holds_during`: inputs `start_time`, `end_time`, `statement`
- `as_of`: inputs `datetime`, `statement`
- `from`: inputs `datetime`, `statement`
- `ultimately`: inputs `statement`

---

## JSON/list/aggregation blocks

- `empty_list`: none
- `head_tail`: inputs `head`, `tail`
- `list_start`: inputs `NAME`
- `list_end`: none
- `list_element`: inputs `element`, `next`
- `collect_list`: inputs `list_name`, `variable_name`, `search`
- `list_aggregation`: fields `aggregation`; inputs `output`, `list`
