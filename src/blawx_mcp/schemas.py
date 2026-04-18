"""Pydantic models for Reasoner "facts" payload shapes.

The Blawx ask endpoints ultimately pass the request JSON payload into
`apps.reasoner.views.json_2_scasp(payload, project=...)`.

That function expects the request body to be a *top-level JSON array* (facts list):

    [
      {"type": "true", "category": "person", "object": "jason"},
      {"type": "false", "relationship": "friend", "parameter1": "jason", "parameter2": {"variable": "one"}}
    ]

These models are used to:
- validate payloads client-side, and
- generate a JSON Schema (via Pydantic v2) that can be surfaced as an MCP tool input spec.
"""

from __future__ import annotations

import json
from typing import Any, List, Optional, Union
from typing_extensions import Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel


class BlawxWorkspacePayload(BaseModel):
    """Shared payload shape for Blawx Blockly workspace writes.

    The payload must include only `blawx_json`.
    """

    model_config = ConfigDict(extra="forbid")

    blawx_json: dict[str, Any] = Field(
        ...,
        description="Blawx visual blocks JSON for the encoding part.",
    )


class EncodingPartUpdatePayload(BlawxWorkspacePayload):
    """Payload for encoding part writes."""


class NamedWorkspacePayload(BlawxWorkspacePayload):
    """Shared payload for named workspace resources.

    Questions and fact scenarios require `name` and `slug` in addition to
    `blawx_json`.
    """

    name: str = Field(..., description="Human-readable name for the resource.")
    slug: str = Field(..., description="URL-safe slug for the resource.")


class FactScenarioPayload(NamedWorkspacePayload):
    """Payload for fact scenario create/update writes."""


class QuestionPayload(NamedWorkspacePayload):
    """Payload for question create/update writes.

    Expected convention: include a single outer question block in `blawx_json`.
    """

    shared: Optional[bool] = Field(
        None,
        description=(
            "Whether this question is shared. Shared questions are discoverable via "
            "shared-question read endpoints and are required for "
            "`blawx_question_ask_with_fact_scenario` and "
            "`blawx_question_ask_with_facts` in the current Blawx app."
        ),
    )


class LegalDocPayload(BaseModel):
    """Payload for legal doc create/update writes."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Human-readable name for the legal document.")
    slug: str = Field(..., description="Short identifier used for citations and URLs.")
    tag_ids: list[int] = Field(
        default_factory=list,
        description="Optional list of tag ids to attach to the legal document.",
    )


class LegalDocPartCreatePayload(BaseModel):
    """Payload for legal doc part create writes.

    The API allows an empty payload. When omitted, the server derives defaults such as
    path/depth and links the part to the legal document in the URL.
    """

    model_config = ConfigDict(extra="forbid")

    parent_id: Optional[int] = Field(
        None,
        description="Optional parent part id for nested parts at creation time.",
    )
    element_type: Optional[str] = Field(
        None,
        description="Optional structural label such as Section, Subsection, Paragraph, or Heading.",
    )
    index_text: Optional[str] = Field(
        None,
        description="Optional displayed numbering text such as 41, (1), or (a).",
    )
    text_content: Optional[str] = Field(
        None,
        description="Optional substantive text for the part.",
    )
    include_parent: Optional[bool] = Field(
        None,
        description="Whether context should include parent text when available.",
    )
    include_sibling: Optional[bool] = Field(
        None,
        description="Whether context should include sibling text when available.",
    )
    substantive: Optional[bool] = Field(
        None,
        description="Whether the part is substantive for reasoning purposes.",
    )


class LegalDocPartUpdatePayload(BaseModel):
    """Payload for legal doc part update writes.

    Do not include `parent_id` when updating. The current API rejects re-parenting via
    PUT even when the value is unchanged.
    """

    model_config = ConfigDict(extra="forbid")

    element_type: Optional[str] = Field(
        None,
        description="Optional structural label such as Section, Subsection, Paragraph, or Heading.",
    )
    index_text: Optional[str] = Field(
        None,
        description="Optional displayed numbering text such as 41, (1), or (a).",
    )
    text_content: Optional[str] = Field(
        None,
        description="Optional substantive text for the part.",
    )
    include_parent: Optional[bool] = Field(
        None,
        description="Whether context should include parent text when available.",
    )
    include_sibling: Optional[bool] = Field(
        None,
        description="Whether context should include sibling text when available.",
    )
    substantive: Optional[bool] = Field(
        None,
        description="Whether the part is substantive for reasoning purposes.",
    )


class VariableRef(BaseModel):
    """Represents a variable in the ask payload.

    Example: {"variable": "one"}
    """

    model_config = ConfigDict(extra="forbid")

    variable: str = Field(..., description="Variable name (will be uppercased by the server).")


AskValue = Union[str, int, float, VariableRef]


class CategoryFact(BaseModel):
    """A fact asserting membership in a category.

    Example:
      {"type": "true", "category": "person", "object": "jason"}
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["true", "false", "unknown"] = Field(..., description="One of: true | false | unknown")
    category: str = Field(..., description="Category slug")
    object: AskValue = Field(..., description="Object atom or variable")


class RelationshipFact(BaseModel):
    """A fact asserting a relationship holds (or does not hold / is unknown).

    Example:
      {"type": "true", "relationship": "likes", "parameter1": "jason", "parameter2": {"variable": "x"}}

    Notes:
    - The server enforces the required arity based on the Relationship definition in the DB.
    - Extra parameterN keys beyond that arity will cause an error if populated.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["true", "false", "unknown"] = Field(..., description="One of: true | false | unknown")
    relationship: str = Field(..., description="Relationship slug")

    # The runtime allows up to 10 parameters.
    parameter1: Optional[AskValue] = None
    parameter2: Optional[AskValue] = None
    parameter3: Optional[AskValue] = None
    parameter4: Optional[AskValue] = None
    parameter5: Optional[AskValue] = None
    parameter6: Optional[AskValue] = None
    parameter7: Optional[AskValue] = None
    parameter8: Optional[AskValue] = None
    parameter9: Optional[AskValue] = None
    parameter10: Optional[AskValue] = None


AskFact = Union[CategoryFact, RelationshipFact]


class AskFactsPayload(RootModel[List[AskFact]]):
    """Root model for the ask endpoint request body.

    The ask endpoint expects the request body to be a top-level JSON array.

    Example (as JSON):
      [
        {"type": "true", "category": "person", "object": "jason"},
        {"type": "unknown", "relationship": "nice", "parameter1": "jason"}
      ]
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                [
                    {"type": "true", "category": "entity", "object": "authority"},
                    {
                        "type": "false",
                        "relationship": "contracting_authority",
                        "parameter1": "contract",
                        "parameter2": {"variable": "X"},
                    },
                    {
                        "type": "unknown",
                        "relationship": "estimated_expenditure",
                        "parameter1": "contract",
                        "parameter2": {"variable": "Amount"},
                    },
                ]
            ]
        }
    )


def ask_facts_payload_json_schema_dict() -> dict:
    """Return a JSON Schema dict for the ask endpoint request body (top-level list)."""

    return AskFactsPayload.model_json_schema()


def ask_facts_payload_json_schema() -> str:
    """Return a JSON Schema string for the ask endpoint request body (top-level list)."""

    return json.dumps(ask_facts_payload_json_schema_dict(), indent=2, sort_keys=True)
