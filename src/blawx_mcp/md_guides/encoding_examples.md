For the full authoring/testing loop, use `encoding-process` first.

## Tool touchpoints

- `blawx_encodingpart_get`: inspect existing encoding before replacement
- `blawx_encodingpart_update`: apply adapted examples as `blawx_json`

```yaml
- - Text: "Rock paper scissors is a game played between two players."

- - Text: "There are three signs:"
  - Text: "Rock,"
    Encoding: |
      {"blocks":{"languageVersion":0,"blocks":[{"type":"unattributed_fact","inputs":{"statements":{"block":{"type":"object_declaration","extraState":{"category_name":"sign"},"fields":{"prefix":"","object_name":"rock","postfix":"is a sign"}}}}}]}}
  - Text: "Paper, and"
    Encoding: |
      {"blocks":{"languageVersion":0,"blocks":[{"type":"unattributed_fact","inputs":{"statements":{"block":{"type":"object_declaration","extraState":{"category_name":"sign"},"fields":{"prefix":"","object_name":"paper","postfix":"is a sign"}}}}}]}}
  - Text: "Scissors."
    Encoding: |
      {"blocks":{"languageVersion":0,"blocks":[{"type":"unattributed_fact","inputs":{"statements":{"block":{"type":"object_declaration","extraState":{"category_name":"sign"},"fields":{"prefix":"","object_name":"scissors","postfix":"is a sign"}}}}}]}}

- - Text: "The signs have the following defeating relationships:"
  - Text: "Rock beats Scissors,"
    Encoding: |
      {"blocks":{"languageVersion":0,"blocks":[{"type":"unattributed_fact","inputs":{"statements":{"block":{"type":"relationship_selector2","extraState":{"relationship_name":"beats","arity":2,"parameter_types":["sign","sign"]},"fields":{"prefix":"","postfix1":"beats","postfix2":""},"inputs":{"parameter1":{"block":{"type":"object_selector","fields":{"object_name":"rock"}}},"parameter2":{"block":{"type":"object_selector","fields":{"object_name":"scissors"}}}}}}}}]}}
  - Text: "Paper beats Rock, and"
    Encoding: |
      {"blocks":{"languageVersion":0,"blocks":[{"type":"unattributed_fact","inputs":{"statements":{"block":{"type":"relationship_selector2","extraState":{"relationship_name":"beats","arity":2,"parameter_types":["sign","sign"]},"fields":{"prefix":"","postfix1":"beats","postfix2":""},"inputs":{"parameter1":{"block":{"type":"object_selector","fields":{"object_name":"paper"}}},"parameter2":{"block":{"type":"object_selector","fields":{"object_name":"rock"}}}}}}}}]}}
  - Text: "Scissors beats Paper."
    Encoding: |
      {"blocks":{"languageVersion":0,"blocks":[{"type":"unattributed_fact","inputs":{"statements":{"block":{"type":"relationship_selector2","extraState":{"relationship_name":"beats","arity":2,"parameter_types":["sign","sign"]},"fields":{"prefix":"","postfix1":"beats","postfix2":""},"inputs":{"parameter1":{"block":{"type":"object_selector","fields":{"object_name":"scissors"}}},"parameter2":{"block":{"type":"object_selector","fields":{"object_name":"paper"}}}}}}}}]}}

- - Text: "The winner of a game is the player who throws the sign that beats the sign thrown by the other player."
    Encoding: |
      {"blocks":{"blocks":[{"type":"attributed_rule","fields":{"defeasible":false,"inapplicable":false},"inputs":{"source":{"block":{"type":"doc_selector","fields":{"doc_part_name":"RPSA Section 4."},"extraState":{"section_reference":"ldp_21"}}},"conclusion":{"block":{"type":"relationship_selector2","fields":{"prefix":"the winner of","postfix1":"was","postfix2":""},"inputs":{"parameter1":{"block":{"type":"variable","fields":{"variable_name":"Game"}}},"parameter2":{"block":{"type":"variable","fields":{"variable_name":"Player"}}}},"extraState":{"arity":2,"parameter_types":["game","player"],"relationship_name":"winner"}}},"conditions":{"block":{"next":{"block":{"next":{"block":{"next":{"block":{"next":{"block":{"next":{"block":{"type":"relationship_selector2","fields":{"prefix":"","postfix1":"beats","postfix2":""},"inputs":{"parameter1":{"block":{"type":"variable","fields":{"variable_name":"Sign1"}}},"parameter2":{"block":{"type":"variable","fields":{"variable_name":"Sign2"}}}},"extraState":{"arity":2,"parameter_types":["sign","sign"],"relationship_name":"beats"}}},"type":"relationship_selector3","fields":{"prefix":"","postfix1":"threw","postfix2":"in","postfix3":""},"inputs":{"parameter1":{"block":{"type":"variable","fields":{"variable_name":"Player2"}}},"parameter2":{"block":{"type":"variable","fields":{"variable_name":"Sign2"}}},"parameter3":{"block":{"type":"variable","fields":{"variable_name":"Game"}}}},"extraState":{"arity":3,"parameter_types":["player","sign","game"],"relationship_name":"threw"}}},"type":"relationship_selector3","fields":{"prefix":"","postfix1":"threw","postfix2":"in","postfix3":""},"inputs":{"parameter1":{"block":{"type":"variable","fields":{"variable_name":"Player"}}},"parameter2":{"block":{"type":"variable","fields":{"variable_name":"Sign1"}}},"parameter3":{"block":{"type":"variable","fields":{"variable_name":"Game"}}}},"extraState":{"arity":3,"parameter_types":["player","sign","game"],"relationship_name":"threw"}}},"type":"object_category","fields":{"category_name":"game"},"inputs":{"object":{"block":{"type":"variable","fields":{"variable_name":"Game"}}}}},"type":"object_category","fields":{"category_name":"player"},"inputs":{"object":{"block":{"type":"variable","fields":{"variable_name":"Player2"}}}}},"type":"object_category","fields":{"category_name":"player"},"inputs":{"object":{"block":{"type":"variable","fields":{"variable_name":"Player"}}}}}}],"languageVersion":0}}
```