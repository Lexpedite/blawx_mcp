from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Any
from urllib.parse import urljoin

import httpx
from mcp.server.fastmcp import FastMCP

from .config import get_settings
from .guides import (
    BLAWX_BLOCKS_GUIDE_MD,
    BLAWX_JSON_GUIDE_MD,
    ENCODING_EXAMPLES_GUIDE_MD,
    ENCODING_PROCESS_GUIDE_MD,
    ENCODINGPART_GUIDE_MD,
    LEGALDOCS_GUIDE_MD,
    ONTOLOGY_GUIDE_MD,
    SCA_SP_GUIDE_MD,
    VALID_BLAWX_JSON_GUIDE_MD,
)
from .schemas import (
    AskFactsPayload,
    EncodingPartUpdatePayload,
    FactScenarioPayload,
    LegalDocPartCreatePayload,
    LegalDocPartUpdatePayload,
    LegalDocPayload,
    QuestionPayload,
)

_TEAM_ID_CACHE: dict[tuple[str, str], int] = {}
_PROJECT_ID_ERROR = "project_id must be a positive integer. Discover valid ids with blawx_projects_list."


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"Invalid integer for {name}: {raw!r}") from exc


def _get_mcp_bind_settings() -> tuple[str, int]:
    host = os.environ.get("BLAWX_MCP_HOST", "127.0.0.1").strip() or "127.0.0.1"
    port = _env_int("BLAWX_MCP_PORT", 8765)
    return host, port


_host, _port = _get_mcp_bind_settings()
_log_level = os.environ.get("BLAWX_MCP_LOG_LEVEL", "INFO").upper()

mcp = FastMCP(
    "blawx-mcp",
    host=_host,
    port=_port,
    log_level=_log_level if _log_level else "INFO",
)


@mcp.tool()
async def blawx_encoding_guide(topic: str = "quickstart") -> dict[str, Any]:
    """Read this first before project-scoped encoding work.

    Use this tool before project-scoped legal-doc, encoding, ontology, question,
    fact-scenario, or ask/answer work to learn:
    - mandatory first step: call `blawx_teams_list`, choose a `team_slug`,
      then call `blawx_projects_list` and choose a `project_id`
    - primary end-to-end workflow (`encoding-process`)
    - required request shape (`blawx_json` key only)
    - Blawx JSON formatting expectations
    - supporting reference guides

    `blawx_health` and `blawx_encoding_guide` are the only tools that do not require
    a `team_slug` and `project_id` discovered with `blawx_teams_list` and
    `blawx_projects_list`.

    Topics: quickstart | blawx-json | valid-blawx-json | blawx-blocks | encodingpart | encoding-process | encoding-examples | ontology | legaldocs | scasp | all
    """

    available_topics = [
        "quickstart",
        "blawx-json",
        "valid-blawx-json",
        "blawx-blocks",
        "encodingpart",
        "encoding-process",
        "encoding-examples",
        "ontology",
        "legaldocs",
        "scasp",
        "all",
    ]

    normalized = topic.strip().lower()
    guides = {
        "scasp": SCA_SP_GUIDE_MD,
        "ontology": ONTOLOGY_GUIDE_MD,
        "blawx-json": BLAWX_JSON_GUIDE_MD,
        "valid-blawx-json": VALID_BLAWX_JSON_GUIDE_MD,
        "blawx-blocks": BLAWX_BLOCKS_GUIDE_MD,
        "encodingpart": ENCODINGPART_GUIDE_MD,
        "encoding-process": ENCODING_PROCESS_GUIDE_MD,
        "encoding-examples": ENCODING_EXAMPLES_GUIDE_MD,
        "legaldocs": LEGALDOCS_GUIDE_MD,
    }

    quickstart = (
        "First call `blawx_teams_list`. If it returns exactly one team, use that team's `slug` as `team_slug`; "
        "if it returns multiple teams and the user has not identified one, ask which team to use. "
        "Then call `blawx_projects_list` with `team_slug` and choose the `project_id` you will pass to every project-scoped tool. "
        "Every tool except `blawx_health`, `blawx_teams_list`, and `blawx_encoding_guide` requires both `team_slug` and `project_id`.\n"
        "Then start with `encoding-process` for the canonical workflow.\n"
        "Then read `encodingpart` for write-tool contract details.\n"
        "Then read `blawx-json` and `blawx-blocks` for block-shape guidance.\n"
        "Use `valid-blawx-json` and `encoding-examples` for concrete patterns.\n"
        "Use `legaldocs` for LegalDocPart granularity, hierarchy planning, and context-field guidance.\n"
        "Use `blawx_encodingpart_get` to inspect current encoding first, after selecting `team_slug` and `project_id`.\n"
        "When writing, call `blawx_encodingpart_update` with only this shape:\n"
        "`{\"blawx_json\": <json object>}`\n"
        "Do not send `content`, `scasp_encoding`, or stringified JSON.\n"
        "If ontology terms are unclear, read `ontology` before writing blocks."
    )

    if normalized == "quickstart":
        selected = quickstart
    elif normalized == "all":
        selected = (
            "# Mandatory First Step\n"
            "Call `blawx_teams_list` before any project-scoped tool. If it returns exactly one team, use "
            "that team's `slug` as `team_slug`; if it returns multiple teams and the user has not identified "
            "one, ask which team to use. Then call `blawx_projects_list` with `team_slug`. Every tool except "
            "`blawx_health`, `blawx_teams_list`, and `blawx_encoding_guide` requires both `team_slug` and "
            "a `project_id` returned by that call.\n\n"
            "# Quickstart\n"
            f"{quickstart}\n\n"
            "# EncodingPart Workflow\n"
            f"{ENCODINGPART_GUIDE_MD}\n\n"
            "# Encoding Process\n"
            f"{ENCODING_PROCESS_GUIDE_MD}\n\n"
            "# LegalDocs and LegalDocParts\n"
            f"{LEGALDOCS_GUIDE_MD}\n\n"
            "# Blawx JSON Blocks\n"
            f"{BLAWX_JSON_GUIDE_MD}\n\n"
            "# Valid Blawx JSON Examples\n"
            f"{VALID_BLAWX_JSON_GUIDE_MD}\n\n"
            "# Blawx Blocks Reference\n"
            f"{BLAWX_BLOCKS_GUIDE_MD}\n\n"
            "# Ontology\n"
            f"{ONTOLOGY_GUIDE_MD}\n\n"
            "# Encoding Examples\n"
            f"{ENCODING_EXAMPLES_GUIDE_MD}\n\n"
            "# s(CASP)\n"
            f"{SCA_SP_GUIDE_MD}"
        )
    elif normalized in guides:
        selected = guides[normalized]
    else:
        return {
            "ok": False,
            "error": "Unknown topic",
            "requested_topic": topic,
            "available_topics": available_topics,
        }

    return {
        "ok": True,
        "topic": normalized,
        "guidance_markdown": selected,
        "available_topics": available_topics,
    }


async def _request_body(
    *,
    method: str,
    url: str,
    api_key: str,
    json_body: Any | None = None,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """HTTP helper for tools that should not expose request details.

    Returns only status information and parsed body.
    """

    headers = _auth_headers(api_key)
    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
        )

    body = await _get_json_or_text(resp)
    return {
        "status_code": resp.status_code,
        "ok": resp.is_success,
        "body": body,
    }


def _validate_slice(start: int | None, end: int | None) -> None:
    if start is not None and start < 1:
        raise ValueError("start must be >= 1 when provided")
    if end is not None and end < 1:
        raise ValueError("end must be >= 1 when provided")
    if start is not None and end is not None and end < start:
        raise ValueError("end must be >= start when both are provided")


def _extract_cache_key(body: Any) -> str:
    if isinstance(body, dict):
        for key in ("cache_key", "cacheKey", "cacheKeyString"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    raise RuntimeError("Response did not include a cache_key")


def _unexpected_response_result(
    resp: dict[str, Any],
    *,
    error: str,
    note: str,
    **extra: Any,
) -> dict[str, Any]:
    result = {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "error": error,
        "note": note,
        "body": resp.get("body"),
    }
    result.update(extra)
    return result


def _extract_optional_int(body: Any, key: str) -> int | None:
    if isinstance(body, dict):
        value = body.get(key)
        if isinstance(value, int):
            return value
    return None


def _extract_optional_str(body: Any, key: str) -> str | None:
    if isinstance(body, dict):
        value = body.get(key)
        if isinstance(value, str):
            return value
    return None


def _extract_index_list(body: Any, *, preferred_keys: tuple[str, ...]) -> list[int] | None:
    """Best-effort extraction of indices from unknown response shapes."""

    if isinstance(body, list):
        return list(range(len(body)))

    if isinstance(body, dict):
        for key in preferred_keys:
            value = body.get(key)
            if isinstance(value, list):
                return list(range(len(value)))

        # Common pagination style
        results = body.get("results")
        if isinstance(results, list):
            return list(range(len(results)))

        # Sometimes a count is provided without an explicit list
        count = body.get("count")
        if isinstance(count, int) and count >= 0:
            return list(range(count))

    return None


_PART_INTERNAL_TO_PUBLIC: dict[str, str] = {
    "HumanModel": "model",
    "HumanAttributes": "attributes",
    "HumanTree": "explanation",
    "constraint_satisfaction": "constraint_satisfaction",
}


def _public_part_name(internal: str) -> str:
    return _PART_INTERNAL_TO_PUBLIC.get(internal, internal)


def _annotate_blawx_json_error(result: dict[str, Any]) -> dict[str, Any]:
    """Append guidance for write responses that include validation issues.

    Guidance is added when:
    - the write response is an error (`ok` is False),
    - an error body indicates expected `extraState` variables, or
    - the response body includes validation warnings (including on success).

    The original response payload is preserved unchanged except for an added
    `guidance` key when any of the above conditions is true.
    """
    body = result.get("body")
    body_dict = body if isinstance(body, dict) else {}
    has_expected_extra_state = any(
        key in body_dict
        for key in (
            "expected_extra_state",
            "expected_extrastate",
            "expected_extra_state_keys",
            "expected_extrastate_keys",
        )
    )
    has_warnings = any(key in body_dict for key in ("warnings", "validation_warnings"))

    guidance_parts: list[str] = []

    if not result.get("ok"):
        guidance_parts.append(
            "This error was returned by the Blawx server for a blawx_json write. "
            "To understand and fix the problem, call `blawx_encoding_guide` with "
            "one or more of these topics:\n"
            "- 'blawx-blocks'  - complete block-type reference (required fields, inputs, extraState)\n"
            "- 'blawx-json'    - JSON block shape and key constraints\n"
            "- 'valid-blawx-json' - validated payload examples\n"
            "- 'encoding-examples' - end-to-end encoding examples\n"
            "- 'encoding-process' - recommended authoring workflow\n"
            "Fix the issues described in 'body' above, then retry."
        )

    if has_expected_extra_state:
        guidance_parts.append(
            "The response includes expected extraState variables. Add those keys "
            "to the relevant block's extraState object exactly as provided by the "
            "server, then retry. For required extraState patterns by block type, "
            "use `blawx_encoding_guide` topic 'blawx-blocks'."
        )

    if has_warnings:
        guidance_parts.append(
            "The response includes validation warnings. In particular, warnings "
            "about missing 'next' blocks indicate a statement input likely expects "
            "a chained statement block. Review statement stacking (`next`) and "
            "conjunction patterns in `blawx_encoding_guide` topics 'blawx-json' "
            "and 'blawx-blocks'."
        )

    if guidance_parts:
        result["guidance"] = "\n\n".join(guidance_parts)

    return result


async def _get_json_or_text(resp: httpx.Response) -> Any:
    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type.lower():
        try:
            return resp.json()
        except Exception:
            return resp.text
    return resp.text


def _auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Api-Key {api_key}",
        "Accept": "application/json, text/plain;q=0.9, */*;q=0.8",
    }


def _validate_project_id(project_id: int) -> int:
    if not isinstance(project_id, int) or project_id < 1:
        raise ValueError(_PROJECT_ID_ERROR)
    return project_id


def _project_api_url(*, base_url: str, team_id: int, project_id: int, path: str = "") -> str:
    validated_project_id = _validate_project_id(project_id)
    suffix = path.lstrip("/")
    base = f"{base_url}/api/teams/{team_id}/projects/{validated_project_id}/"
    return f"{base}{suffix}"


def _project_reasoner_url(*, base_url: str, team_slug: str, project_id: int, path: str = "") -> str:
    validated_project_id = _validate_project_id(project_id)
    suffix = path.lstrip("/")
    base = f"{base_url}/a/{team_slug}/project/{validated_project_id}/"
    return f"{base}{suffix}"


async def _request_json(
    *,
    method: str,
    url: str,
    api_key: str,
    json_body: Any | None = None,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    headers = _auth_headers(api_key)
    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
        )

    body = await _get_json_or_text(resp)
    return {
        "url": url,
        "params": params,
        "request": json_body,
        "request_headers": {
            "authorization": "Api-Key <redacted>",
            "accept": headers.get("Accept"),
        },
        "status_code": resp.status_code,
        "ok": resp.is_success,
        "body": body,
        "headers": {
            "content-type": resp.headers.get("content-type"),
            "www-authenticate": resp.headers.get("www-authenticate"),
            "location": resp.headers.get("location"),
        },
    }


async def _resolve_team_id(*, base_url: str, api_key: str, team_slug: str) -> int:
    cached = _TEAM_ID_CACHE.get((api_key, team_slug))
    if cached is not None:
        return cached

    # Paginated endpoint: /teams/api/teams/
    url = f"{base_url}/teams/api/teams/"
    timeout = httpx.Timeout(20.0)
    headers = _auth_headers(api_key)

    async with httpx.AsyncClient(timeout=timeout) as client:
        while True:
            resp = await client.get(url, headers=headers)
            if not resp.is_success:
                body = await _get_json_or_text(resp)
                raise RuntimeError(
                    f"Failed to list teams (status {resp.status_code}) while resolving team slug {team_slug!r}: {body}"
                )
            data = resp.json() if resp.headers.get("content-type", "").lower().startswith("application/json") else {}
            results = data.get("results") or []
            for team in results:
                if isinstance(team, dict) and team.get("slug") == team_slug:
                    team_id = int(team["id"])
                    _TEAM_ID_CACHE[(api_key, team_slug)] = team_id
                    return team_id

            next_url = data.get("next")
            if not next_url:
                break
            url = next_url

    raise RuntimeError(
        f"Team slug {team_slug!r} not found in /teams/api/teams/ results for this API key."
    )


async def _project_request_json(
    *,
    method: str,
    project_id: int,
    team_slug: str,
    api_path: str,
    json_body: Any | None = None,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url,
        api_key=settings.api_key,
        team_slug=team_slug,
    )
    url = _project_api_url(
        base_url=settings.base_url,
        team_id=team_id,
        project_id=project_id,
        path=api_path,
    )
    return await _request_json(
        method=method,
        url=url,
        api_key=settings.api_key,
        json_body=json_body,
        params=params,
        timeout_seconds=timeout_seconds,
    )


async def _project_request_body(
    *,
    method: str,
    project_id: int,
    team_slug: str,
    reasoner_path: str,
    json_body: Any | None = None,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    settings = get_settings()
    url = _project_reasoner_url(
        base_url=settings.base_url,
        team_slug=team_slug,
        project_id=project_id,
        path=reasoner_path,
    )
    return await _request_body(
        method=method,
        url=url,
        api_key=settings.api_key,
        json_body=json_body,
        params=params,
        timeout_seconds=timeout_seconds,
    )


async def _project_reasoner_request_json(
    *,
    method: str,
    project_id: int,
    team_slug: str,
    reasoner_path: str,
    json_body: Any | None = None,
    params: dict[str, Any] | list[tuple[str, Any]] | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    settings = get_settings()
    url = _project_reasoner_url(
        base_url=settings.base_url,
        team_slug=team_slug,
        project_id=project_id,
        path=reasoner_path,
    )
    return await _request_json(
        method=method,
        url=url,
        api_key=settings.api_key,
        json_body=json_body,
        params=params,
        timeout_seconds=timeout_seconds,
    )


@mcp.tool()
async def blawx_health() -> dict[str, Any]:
    """Check Blawx app health. 
    """
    settings = get_settings()
    base_url = settings.base_url
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    url = urljoin(base_url, "health/")

    return await _request_json(
        method="GET",
        url=url,
        api_key=settings.api_key,
        timeout_seconds=10.0,
    )


@mcp.tool()
async def blawx_teams_list() -> dict[str, Any]:
    """List teams available to the configured API key.

    Call this tool before team-scoped work. If exactly one team is returned, use
    that team's `slug` as `team_slug`. If multiple teams are returned and the
    user has not identified a team, ask the user which team to use.
    """

    settings = get_settings()
    url = f"{settings.base_url}/teams/api/teams/"
    result = await _request_json(
        method="GET",
        url=url,
        api_key=settings.api_key,
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "Start here for team-scoped work. If exactly one team is returned, use its "
            "`slug` as `team_slug`. If multiple teams are returned and the user has not "
            "already identified a team, ask the user which team to use before calling "
            "blawx_projects_list or other project-scoped tools."
        ),
        "next_recommended_tool": "blawx_projects_list",
    }


@mcp.tool()
async def blawx_projects_list(team_slug: str) -> dict[str, Any]:
    """List projects available under a team.

    Call `blawx_teams_list` first, then call this tool with the selected team slug
    for any project-scoped work.

    `team_slug` is required and should be obtained from `blawx_teams_list`.
    Every project-scoped tool requires this same `team_slug` and a `project_id`
    returned here.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url,
        api_key=settings.api_key,
        team_slug=team_slug,
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/"
    result = await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)
    return {
        **result,
        "workflow_hint": (
            "After choosing `team_slug` with blawx_teams_list, pick a project id from this list and pass it as `project_id` "
            "to every downstream project-scoped tool together with this `team_slug`. Only "
            "blawx_health, blawx_teams_list, and blawx_encoding_guide do not require both."
        ),
        "next_recommended_tool": "blawx_project_detail",
    }


@mcp.tool()
async def blawx_project_detail(team_slug: str, project_id: int) -> dict[str, Any]:
    """Get metadata for a single project id obtained from blawx_projects_list.

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.
    """

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_list(team_slug: str, project_id: int) -> dict[str, Any]:
    """List ontology (available categories and relationships).

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.
    """
    result = await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="ontology/",
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This tool is project-scoped. Obtain `project_id` from blawx_projects_list first, "
            "then use category/relationship detail tools for specific ids from this list."
        ),
        "next_recommended_tool": "blawx_ontology_category_detail",
    }


@mcp.tool()
async def blawx_ontology_categories_list(team_slug: str, project_id: int) -> dict[str, Any]:
    """List ontology categories.

    This endpoint is read-write in the API (create/update/delete are also supported).
    """

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="ontology/categories/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_category_create(team_slug: str, project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new ontology category.

        Pass the ontology category JSON body as `payload`.

        Current API validation requires `name` and `slug`.
        Common payload shape:
        {
            "name": "Contract",
            "slug": "contract",
            "short_description": "",
            "nlg_prefix": "",
            "nlg_postfix": "is a contract"
        }

        `nlg_postfix` is currently limited to 50 characters by the Blawx API.
    """

    return await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path="ontology/categories/",
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_category_update(team_slug: str, project_id: int, category_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace an ontology category (PUT)."""

    return await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/categories/{category_id}/",
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_category_delete(team_slug: str, project_id: int, category_id: int) -> dict[str, Any]:
    """Delete an ontology category."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/categories/{category_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_category_detail(team_slug: str, project_id: int, category_id: int) -> dict[str, Any]:
    """Get category details by id obtained from blawx_ontology_list tool.
    """
    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/categories/{category_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_detail(team_slug: str, project_id: int, relationship_id: int) -> dict[str, Any]:
    """Get relationship details by id obtained from blawx_ontology_list tool.
    """
    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationships_list(team_slug: str, project_id: int) -> dict[str, Any]:
    """List ontology relationships."""

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="ontology/relationships/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_create(team_slug: str, project_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new ontology relationship.

    Pass the ontology relationship JSON body as `payload`.

    Current API validation requires `name` and `slug`.
    Common payload shape:
    {
      "name": "Estimated Expenditure",
      "slug": "estimated_expenditure",
      "short_description": "",
      "nlg_prefix": ""
    }
    """

    return await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path="ontology/relationships/",
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_update(team_slug: str, project_id: int, relationship_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace an ontology relationship (PUT)."""

    return await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/",
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_delete(team_slug: str, project_id: int, relationship_id: int) -> dict[str, Any]:
    """Delete an ontology relationship."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameters_list(team_slug: str, project_id: int, relationship_id: int) -> dict[str, Any]:
    """List parameters for a relationship."""

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/parameters/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameter_create(team_slug: str, project_id: int, relationship_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new relationship parameter definition.

    Pass the relationship-parameter JSON body as `payload`.

    Current API validation requires `order` and `type_id`.
    Common payload shape:
    {
      "order": 1,
      "type_id": 466,
      "nlg_postfix": ""
    }

    `type_id` must be the id of an ontology category.
    """

    return await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/parameters/",
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameter_update(
    team_slug: str,
    project_id: int, relationship_id: int, parameter_id: int, payload: dict[str, Any]
) -> dict[str, Any]:
    """Replace a relationship parameter definition (PUT)."""

    return await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/parameters/{parameter_id}/",
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameter_detail(team_slug: str, project_id: int, relationship_id: int, parameter_id: int) -> dict[str, Any]:
    """Get a relationship parameter definition by id."""

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/parameters/{parameter_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameter_delete(team_slug: str, project_id: int, relationship_id: int, parameter_id: int) -> dict[str, Any]:
    """Delete a relationship parameter definition."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"ontology/relationships/{relationship_id}/parameters/{parameter_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_fact_scenarios_list(team_slug: str, project_id: int) -> dict[str, Any]:
    """List available fact scenarios for use in the blawx_question_ask_with_fact_scenario tool.
    """
    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="facts/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_fact_scenario_create(team_slug: str, project_id: int, payload: FactScenarioPayload) -> dict[str, Any]:
    """Create a new fact scenario.

    Uses the same workspace payload shape as `blawx_encodingpart_update`.
    """

    return _annotate_blawx_json_error(await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path="facts/",
        json_body=payload.model_dump(),
        timeout_seconds=30.0,
    ))


@mcp.tool()
async def blawx_fact_scenario_detail(team_slug: str, project_id: int, fact_scenario_id: int) -> dict[str, Any]:
    """Get fact scenario details by id obtained from blawx_fact_scenarios_list tool.
    """
    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"facts/{fact_scenario_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_fact_scenario_update(
    team_slug: str,
    project_id: int, fact_scenario_id: int, payload: FactScenarioPayload
) -> dict[str, Any]:
    """Replace a fact scenario (PUT).

    Uses the same workspace payload shape as `blawx_encodingpart_update`.
    """

    return _annotate_blawx_json_error(await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"facts/{fact_scenario_id}/",
        json_body=payload.model_dump(),
        timeout_seconds=30.0,
    ))


@mcp.tool()
async def blawx_fact_scenario_delete(team_slug: str, project_id: int, fact_scenario_id: int) -> dict[str, Any]:
    """Delete a fact scenario."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"facts/{fact_scenario_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_questions_list(team_slug: str, project_id: int) -> dict[str, Any]:
    """List available shared questions (read-only).

    For read-write question management, use blawx_questions_list_all and related tools.
    """
    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="questions/shared/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_questions_list_all(team_slug: str, project_id: int) -> dict[str, Any]:
    """List all questions in the project (read-write collection)."""

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="questions/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_question_detail(team_slug: str, project_id: int, question_id: int) -> dict[str, Any]:
    """Get question by id obtained from blawx_questions_list tool.
    """
    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"questions/shared/{question_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_question_detail_all(team_slug: str, project_id: int, question_id: int) -> dict[str, Any]:
    """Get a question from the read-write questions endpoint by id."""

    return await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"questions/{question_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_question_create(team_slug: str, project_id: int, payload: QuestionPayload) -> dict[str, Any]:
    """Create a new question in the project.

    Uses the same workspace payload shape as `blawx_encodingpart_update`.
    A question encoding is expected to include one outer question block.
    """

    return _annotate_blawx_json_error(await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path="questions/",
        json_body=payload.model_dump(),
        timeout_seconds=30.0,
    ))


@mcp.tool()
async def blawx_question_update(team_slug: str, project_id: int, question_id: int, payload: QuestionPayload) -> dict[str, Any]:
    """Replace a question (PUT).

    Uses the same workspace payload shape as `blawx_encodingpart_update`.
    A question encoding is expected to include one outer question block.
    """

    return _annotate_blawx_json_error(await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"questions/{question_id}/",
        json_body=payload.model_dump(),
        timeout_seconds=30.0,
    ))


@mcp.tool()
async def blawx_question_delete(team_slug: str, project_id: int, question_id: int) -> dict[str, Any]:
    """Delete a question."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"questions/{question_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_question_ask_with_fact_scenario(team_slug: str, project_id: int, question_id: int, fact_scenario_id: int) -> dict[str, Any]:
    """Ask a question using a stored fact scenario.

        Returns a cache key for later retrieval.

        If the Blawx server returns an unexpected response shape instead of a cached-response
        payload, this tool returns the raw server response in `body` together with an `error`
        and `note` describing what was expected.

        Notes:
            - In the current Blawx app, this route works only with shared questions.
                Non-shared questions may return `Question not available via API.`
            - The returned results are temporary. When available, `ttl_seconds` indicates how long
                the cached response is expected to remain available.
            - If follow-up retrieval tools return `status_code` 410 (expired / not found), re-run
                this tool (or `blawx_question_ask_with_facts`) to obtain a fresh cache key.
    """
    payload = {"facts": fact_scenario_id}
    resp = await _project_request_body(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=f"questions/{question_id}/ask/qfa/",
        params={"output_styles": ["human"], "cached": True},
        json_body=payload,
        timeout_seconds=120.0,
    )

    body = resp.get("body")
    try:
        cache_key = _extract_cache_key(body)
    except RuntimeError:
        return _unexpected_response_result(
            resp,
            error="Expected cached ask response including cache_key, but Blawx returned a different response.",
            note=(
                "The raw Blawx response is preserved in `body`. This usually means the ask endpoint "
                "returned an error payload, a non-cached response, or a response schema this MCP server "
                "does not recognize."
            ),
        )
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "cache_key": cache_key,
        "body": body,
        "ttl_seconds": _extract_optional_int(body, "ttl_seconds"),
        "created_at": _extract_optional_str(body, "created_at"),
        "answer_count": _extract_optional_int(body, "answer_count"),
    }


@mcp.tool()
async def blawx_question_ask_with_facts(team_slug: str, project_id: int, question_id: int, facts: AskFactsPayload) -> dict[str, Any]:
    """Ask a question using a structured facts payload.

        Returns a cache key for later retrieval.

        If the Blawx server returns an unexpected response shape instead of a cached-response
        payload, this tool returns the raw server response in `body` together with an `error`
        and `note` describing what was expected.

        Notes:
            - In the current Blawx app, this route also works only with shared questions.
                Non-shared questions may return `Question not available via API.`
            - The returned results are temporary. When available, `ttl_seconds` indicates how long
                the cached response is expected to remain available.
            - If follow-up retrieval tools return `status_code` 410 (expired / not found), re-run
                this tool (or `blawx_question_ask_with_fact_scenario`) to obtain a fresh cache key.

    The target server is an answer set programming reasoner, so the facts
    have the meanings they would be afforded in answer set programming.

    Facts have a type that corresponds to answer set programming truth values:
        "true" - the fact is known to be true
        "false" - the fact is known to be false
        "unknown" - the server should consider the possibility of both truth and falsehood
    
    Be careful to encode only facts that you are generating, do not encode facts that have been
    obtained from previous calls to the reasoner.

    The server will accept ungrounded facts, using variables with names. These variables
    have the meaning that they would be given in logic programming. Two variables with the same name
    refer to the same entity. Variables with different names may refer to different entities, or
    the same entity. However, each fact is scoped individually, so variables used across multiple facts
    have no relationship to one another.
    
    It is seldom useful to say that something is true about everything, or false
    about everything, so be reluctant to use variables in true or false statements unless you
    are sure that is the intent.

    Unknown statements are used to facilitate abducible reasoning by creating an even loop over negation,
    an unknown statement is converted into two rules, if there is no evidence the thing is true, it is false,
    and if there is no evidence it is false, it is true, and the server explores both possibilities.

    Using a large number of unknown statements may cause the reasoner to time out.

    Format values according to these rules:

    1. OBJECTS (for non-datatype categories):
        - Must be declared in category facts before being used in relationships
        - Object names must be lowercase strings without spaces (e.g., "john_doe", "contract_main", "department_of_defence")
        - Convert user's natural language to valid atoms by replacing spaces with underscores
        - Use only lowercase letters, numbers, and underscores
        - Do not end a symbol with an underscore followed by numbers, as that is a reserved format.

    2. DATATYPE VALUES (for Number, Date, Datetime, Time, Duration categories):
        - Do NOT declare these in category facts
        - Do NOT convert to atoms
        - Use the values directly in relationships as shown below:
    
        Numbers: Plain integers or decimals (e.g., 10000, 3750000.50, 200000)
        Dates: ISO 8601 format YYYY-MM-DD (e.g., "2025-01-15", "2024-12-31")
        Times: HH:MM format (e.g., "14:30", "09:00")
        Datetimes: ISO 8601 format YYYY-MM-DDTHH:MM (e.g., "2025-01-15T14:30", "2024-12-31T23:59")
        Durations: ISO 8601 duration format (e.g., "P3D" for 3 days, "PT5H" for 5 hours, "P1DT2H30M" for 1 day, 2 hours, 30 minutes)
    """
    # The underlying endpoint expects the raw list payload, not a wrapper object.
    # `facts.root` contains Pydantic models; dump them to plain JSON-serializable dicts.
    payload = [fact.model_dump(exclude_none=True) for fact in facts.root]
    resp = await _project_request_body(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=f"questions/{question_id}/ask/",
        params={"output_styles": ["human"], "cached": True},
        json_body=payload,
        timeout_seconds=120.0,
    )

    body = resp.get("body")
    try:
        cache_key = _extract_cache_key(body)
    except RuntimeError:
        return _unexpected_response_result(
            resp,
            error="Expected cached ask response including cache_key, but Blawx returned a different response.",
            note=(
                "The raw Blawx response is preserved in `body`. This usually means the ask endpoint "
                "returned an error payload, a non-cached response, or a response schema this MCP server "
                "does not recognize."
            ),
        )
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "cache_key": cache_key,
        "body": body,
        "ttl_seconds": _extract_optional_int(body, "ttl_seconds"),
        "created_at": _extract_optional_str(body, "created_at"),
        "answer_count": _extract_optional_int(body, "answer_count"),
    }


@mcp.tool()
async def blawx_list_answers(team_slug: str, project_id: int, question_id: int, cache_key: str) -> dict[str, Any]:
    """List answers for a previously asked question.

        Returns:
            - total: total number of answers
            - answers: list of {answer_index, bindings, explanation_count}

        If the Blawx server returns an unexpected response shape, the raw server response is
        preserved in `body` and any returned `answers` are only best-effort inferred values.

        If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    resp = await _project_request_body(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=f"questions/{question_id}/responses/{cache_key}/answers/",
        timeout_seconds=60.0,
    )

    body = resp.get("body")
    if isinstance(body, dict) and isinstance(body.get("answers"), list):
        answers_out: list[dict[str, Any]] = []
        for item in body.get("answers") or []:
            if not isinstance(item, dict):
                continue
            answer_index = item.get("answer_index")
            bindings = item.get("bindings")
            explanation_count = item.get("explanation_count")
            if isinstance(answer_index, int) and isinstance(bindings, str) and isinstance(explanation_count, int):
                answers_out.append(
                    {
                        "answer_index": answer_index,
                        "bindings": bindings,
                        "explanation_count": explanation_count,
                    }
                )

        total = body.get("total")
        total_int = total if isinstance(total, int) else len(answers_out)
        return {
            "ok": resp["ok"],
            "status_code": resp["status_code"],
            "total": total_int,
            "answers": answers_out,
        }

    # Fallback for unexpected shapes.
    indices = _extract_index_list(body, preferred_keys=("answers", "Answers"))
    answer_indices = indices or []
    return _unexpected_response_result(
        resp,
        error="Expected answer list response, but Blawx returned a different response shape.",
        note="The raw Blawx response is preserved in `body`. Any returned `answers` values were inferred heuristically.",
        total=len(answer_indices),
        answers=[{"answer_index": i, "bindings": "", "explanation_count": 0} for i in answer_indices],
    )


@mcp.tool()
async def blawx_cached_response_meta(team_slug: str, project_id: int, question_id: int, cache_key: str) -> dict[str, Any]:
    """Retrieve cached-response metadata (ttl, created time, answer count when available).

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _project_reasoner_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=f"questions/{question_id}/responses/{cache_key}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_list_explanations(team_slug: str, project_id: int, question_id: int, cache_key: str, answer_index: int) -> dict[str, Any]:
    """List explanations available for a specific answer.

        Returns:
            - answer_index
            - bindings
            - explanations: list of {explanation_index, parts_available}

        If the Blawx server returns an unexpected response shape, the raw server response is
        preserved in `body` and any returned `explanations` are only best-effort inferred values.

        Important:
            - The explanation text can include variables whose meaning depends on constraints.
                Always retrieve the attributes part for the same explanation when interpreting the
                explanation part; otherwise conclusions may be incorrect.

        If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    resp = await _project_request_body(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=f"questions/{question_id}/responses/{cache_key}/answers/{answer_index}/",
        timeout_seconds=60.0,
    )

    body = resp.get("body")
    if isinstance(body, dict) and isinstance(body.get("explanations"), list):
        out_explanations: list[dict[str, Any]] = []
        for item in body.get("explanations") or []:
            if not isinstance(item, dict):
                continue
            explanation_index_val = item.get("explanation_index")
            if not isinstance(explanation_index_val, int):
                continue

            parts_obj = item.get("parts")
            parts_available: list[str] = []
            if isinstance(parts_obj, dict):
                for internal_name, public_name in _PART_INTERNAL_TO_PUBLIC.items():
                    if internal_name in parts_obj:
                        parts_available.append(public_name)

            out_explanations.append(
                {
                    "explanation_index": explanation_index_val,
                    "parts_available": parts_available,
                }
            )

        bindings = body.get("bindings") if isinstance(body.get("bindings"), str) else ""
        return {
            "ok": resp["ok"],
            "status_code": resp["status_code"],
            "answer_index": answer_index,
            "bindings": bindings,
            "explanations": out_explanations,
        }

    # Fallback for unexpected shapes.
    indices = _extract_index_list(
        body,
        preferred_keys=("explanations", "Explanations", "explanation", "Explanation"),
    )
    explanation_indices = indices or []
    return _unexpected_response_result(
        resp,
        error="Expected explanation list response, but Blawx returned a different response shape.",
        note="The raw Blawx response is preserved in `body`. Any returned `explanations` values were inferred heuristically.",
        answer_index=answer_index,
        bindings="",
        explanations=[{"explanation_index": i, "parts_available": []} for i in explanation_indices],
    )


@mcp.tool()
async def blawx_get_explanation_full(
    team_slug: str,
    project_id: int,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
) -> dict[str, Any]:
    """Get the full explanation object (all parts, unsliced).

    This can be large; prefer blawx_get_*_part tools when you only need one section.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _project_reasoner_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=(
            f"questions/{question_id}/responses/{cache_key}/answers/{answer_index}"
            f"/explanations/{explanation_index}/"
        ),
        timeout_seconds=60.0,
    )


@mcp.tool()
async def blawx_legaldocs_list(team_slug: str, project_id: int) -> dict[str, Any]:
    """List legal docs in the project.

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.

    This returns document-level metadata. To read legislation text, then call:
    1) `blawx_legaldocparts_list` for the chosen legal doc
    2) `blawx_legaldocpart_detail` for each relevant part
    """

    result = await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path="legaldocs/",
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This tool is project-scoped; choose `team_slug` with blawx_teams_list, then obtain `project_id` from blawx_projects_list. "
            "This is a document list. To read legal text, call blawx_legaldocparts_list for a legal_doc_id, "
            "then call blawx_legaldocpart_detail for the relevant part(s). For structure and write fields, "
            "read blawx_encoding_guide topic 'legaldocs'."
        ),
        "next_recommended_tool": "blawx_legaldocparts_list",
    }


@mcp.tool()
async def blawx_legaldoc_create(team_slug: str, project_id: int, payload: LegalDocPayload) -> dict[str, Any]:
    """Create a new legal doc.

    The verified minimum payload requires `name` and `slug`.
    Optional `tag_ids` defaults to an empty list.
    """

    result = await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path="legaldocs/",
        json_body=payload.model_dump(exclude_none=True),
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "After creating a legal doc, inspect it with blawx_legaldoc_detail or create its "
            "parts with blawx_legaldocpart_create. For field details, read blawx_encoding_guide "
            "topic 'legaldocs'."
        ),
        "next_recommended_tool": "blawx_legaldocpart_create",
    }


@mcp.tool()
async def blawx_legaldoc_detail(team_slug: str, project_id: int, legal_doc_id: int) -> dict[str, Any]:
    """Get a legal doc by id.

    This returns document-level metadata. To read the legislative text itself,
    list parts with `blawx_legaldocparts_list` and then fetch part text with
    `blawx_legaldocpart_detail`.
    """

    result = await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/",
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This is legal-doc metadata. To read legal text, call blawx_legaldocparts_list "
            "for this legal_doc_id, then call blawx_legaldocpart_detail for relevant part ids. "
            "Read blawx_encoding_guide topic 'legaldocs' before editing document structure."
        ),
        "next_recommended_tool": "blawx_legaldocparts_list",
    }


@mcp.tool()
async def blawx_legaldoc_update(team_slug: str, project_id: int, legal_doc_id: int, payload: LegalDocPayload) -> dict[str, Any]:
    """Replace a legal doc (PUT)."""

    result = await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/",
        json_body=payload.model_dump(exclude_none=True),
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": "Call blawx_legaldoc_detail or blawx_legaldocparts_list to inspect the updated document.",
        "next_recommended_tool": "blawx_legaldoc_detail",
    }


@mcp.tool()
async def blawx_legaldoc_delete(team_slug: str, project_id: int, legal_doc_id: int) -> dict[str, Any]:
    """Delete a legal doc."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_legaldocparts_list(team_slug: str, project_id: int, legal_doc_id: int) -> dict[str, Any]:
    """List parts for a legal doc.

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.

    This list is mainly navigational metadata (part ids/titles/order). To view the
    actual legislation text for a part, call `blawx_legaldocpart_detail` for that part id.
    """

    result = await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/",
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This tool is project-scoped; choose `team_slug` with blawx_teams_list, then obtain `project_id` from blawx_projects_list. "
            "This is a parts list. To read the actual text, call blawx_legaldocpart_detail for each relevant "
            "legal_doc_part_id. Use blawx_legaldocpart_create to add a new part, and default to one part per "
            "heading, section, subsection, paragraph, or similar legislative unit with distinct text."
        ),
        "next_recommended_tool": "blawx_legaldocpart_detail",
    }


@mcp.tool()
async def blawx_legaldocpart_create(
    team_slug: str,
    project_id: int,
    legal_doc_id: int,
    payload: LegalDocPartCreatePayload,
) -> dict[str, Any]:
    """Create a legal doc part.

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.

    The API allows an empty payload. `parent_id` may be supplied at creation time for nested
    parts; the legal doc linkage itself comes from the URL. One EncodingPart attaches to one
    LegalDocPart, so decide the legislative hierarchy and part boundaries before creating parts.
    """

    result = await _project_request_json(
        method="POST",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/",
        json_body=payload.model_dump(exclude_none=True),
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This tool is project-scoped; choose `team_slug` with blawx_teams_list, then obtain `project_id` from blawx_projects_list. "
            "Create one LegalDocPart per heading, section, subsection, paragraph, or similar legislative "
            "unit when that unit has distinct text. After creating a part, inspect its text with "
            "blawx_legaldocpart_detail or attach an encoding with blawx_encodingpart_update. Read "
            "blawx_encoding_guide topic 'legaldocs' for structure details."
        ),
        "next_recommended_tool": "blawx_encodingpart_update",
    }


@mcp.tool()
async def blawx_legaldocpart_detail(team_slug: str, project_id: int, legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Get a single legal doc part by id.

    Use this tool to view the actual text/content for a legal doc part.
    """

    result = await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/",
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This tool returns the part detail, including the legal text/content when present. "
            "For create/update field behavior, read blawx_encoding_guide topic 'legaldocs'."
        ),
    }


@mcp.tool()
async def blawx_legaldocpart_update(
    team_slug: str,
    project_id: int,
    legal_doc_id: int,
    legal_doc_part_id: int,
    payload: LegalDocPartUpdatePayload,
) -> dict[str, Any]:
    """Replace a legal doc part (PUT).

    Do not include `parent_id` in update payloads. The current API rejects re-parenting via PUT.
    """

    result = await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/",
        json_body=payload.model_dump(exclude_none=True),
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": "Call blawx_legaldocpart_detail to inspect the updated part text and metadata.",
        "next_recommended_tool": "blawx_legaldocpart_detail",
    }


@mcp.tool()
async def blawx_legaldocpart_delete(team_slug: str, project_id: int, legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Delete a legal doc part."""

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/",
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_encodingpart_get(team_slug: str, project_id: int, legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Get the encoding for a specific legal doc part.

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.

    Use `blawx_encoding_guide` first (topic: quickstart, then blawx-json/encodingpart)
    before creating or editing encoding payloads. One EncodingPart attaches to one LegalDocPart,
    so confirm part granularity before editing.
    """

    result = await _project_request_json(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/encoding/",
        timeout_seconds=30.0,
    )
    return {
        **result,
        "workflow_hint": (
            "This tool is project-scoped; choose `team_slug` with blawx_teams_list, then obtain `project_id` from blawx_projects_list. "
            "Use this result to inspect the current encoding before replacing it. If part boundaries are unclear, "
            "read blawx_encoding_guide topics 'legaldocs' and 'encoding-process' before editing."
        ),
        "next_recommended_tool": "blawx_encodingpart_update",
    }


@mcp.tool()
async def blawx_encodingpart_update(
    team_slug: str,
    project_id: int,
    legal_doc_id: int,
    legal_doc_part_id: int,
    payload: EncodingPartUpdatePayload,
) -> dict[str, Any]:
    """Replace the encoding for a legal doc part (PUT).

    `team_slug` should be selected with `blawx_teams_list`; `project_id` should
    be selected with `blawx_projects_list`.

    Read `blawx_encoding_guide` first. This tool accepts only this payload shape:
    {"blawx_json": <json object>}

    Do not send `content`, `scasp_encoding`, or stringified JSON. One EncodingPart attaches
    to one LegalDocPart, so split the legal text into the correct parts before encoding.
    """

    result = _annotate_blawx_json_error(await _project_request_json(
        method="PUT",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/encoding/",
        json_body=payload.model_dump(),
        timeout_seconds=60.0,
    ))
    return {
        **result,
        "workflow_hint": (
            "This tool is project-scoped; choose `team_slug` with blawx_teams_list, then obtain `project_id` from blawx_projects_list. "
            "Write encoding only after confirming the LegalDocPart boundaries are correct, because each "
            "encoding attaches to exactly one part."
        ),
        "next_recommended_tool": "blawx_legaldocpart_detail",
    }


@mcp.tool()
async def blawx_encodingpart_delete(team_slug: str, project_id: int, legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Delete the encoding for a legal doc part.

    Use `blawx_encoding_guide` if you need to recreate the encoding with the correct payload shape.
    """

    return await _project_request_json(
        method="DELETE",
        project_id=project_id,
        team_slug=team_slug,
        api_path=f"legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/encoding/",
        timeout_seconds=60.0,
    )


async def _get_part(
    *,
    team_slug: str,
    project_id: int,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
    part_name: str,
    start: int | None,
    end: int | None,
) -> dict[str, Any]:
    _validate_slice(start, end)
    params: dict[str, Any] = {}
    if start is not None:
        params["start"] = start
    if end is not None:
        params["end"] = end

    resp = await _project_request_body(
        method="GET",
        project_id=project_id,
        team_slug=team_slug,
        reasoner_path=(
            f"questions/{question_id}/responses/{cache_key}/answers/{answer_index}"
            f"/explanations/{explanation_index}/{part_name}/"
        ),
        params=params if params else None,
        timeout_seconds=60.0,
    )
    body = resp.get("body")
    if isinstance(body, dict):
        # Matches CachedResponseExplanationPart.
        return {
            "ok": resp["ok"],
            "status_code": resp["status_code"],
            "part": _public_part_name(str(body.get("part", part_name))),
            "type": body.get("type"),
            "start": body.get("start"),
            "end": body.get("end"),
            "total": body.get("total"),
            "data": body.get("data"),
        }

    # Fallback for non-JSON or unexpected responses.
    return _unexpected_response_result(
        resp,
        error=f"Expected explanation part response for {part_name}, but Blawx returned a different response shape.",
        note="The raw Blawx response is preserved in `body`. `data` mirrors that body for compatibility with existing callers.",
        part=_public_part_name(part_name),
        type=None,
        start=start,
        end=end,
        total=None,
        data=body,
    )


@mcp.tool()
async def blawx_get_model_part(
    team_slug: str,
    project_id: int,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Get the model portion of an explanation.

    Uses optional 1-based inclusive line slicing via start/end.
    Returns an object with fields: part, type, start, end, total, data.

    If the Blawx server returns an unexpected response shape, the raw server response is
    preserved in `body` and mirrored in `data` for compatibility.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
        project_id=project_id,
        team_slug=team_slug,
        question_id=question_id,
        cache_key=cache_key,
        answer_index=answer_index,
        explanation_index=explanation_index,
        part_name="HumanModel",
        start=start,
        end=end,
    )


@mcp.tool()
async def blawx_get_attributes_part(
    team_slug: str,
    project_id: int,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Get the attributes portion of an explanation.

    Uses optional 1-based inclusive line slicing via start/end.
    Returns an object with fields: part, type, start, end, total, data.

    If the Blawx server returns an unexpected response shape, the raw server response is
    preserved in `body` and mirrored in `data` for compatibility.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
        project_id=project_id,
        team_slug=team_slug,
        question_id=question_id,
        cache_key=cache_key,
        answer_index=answer_index,
        explanation_index=explanation_index,
        part_name="HumanAttributes",
        start=start,
        end=end,
    )


@mcp.tool()
async def blawx_get_explanation_part(
    team_slug: str,
    project_id: int,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Get the explanation portion of an explanation.

    Uses optional 1-based inclusive line slicing via start/end.
    Returns an object with fields: part, type, start, end, total, data.

    If the Blawx server returns an unexpected response shape, the raw server response is
    preserved in `body` and mirrored in `data` for compatibility.

        Important:
            - Always review the attributes part for the same explanation. The explanation text can
                include variables whose meaning depends on attribute constraints (or lack of constraints).
                Reading the explanation without attributes can lead to incorrect interpretation.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
        project_id=project_id,
        team_slug=team_slug,
        question_id=question_id,
        cache_key=cache_key,
        answer_index=answer_index,
        explanation_index=explanation_index,
        part_name="HumanTree",
        start=start,
        end=end,
    )


@mcp.tool()
async def blawx_get_constraint_satisfaction_part(
    team_slug: str,
    project_id: int,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
    start: int | None = None,
    end: int | None = None,
) -> dict[str, Any]:
    """Get the constraint satisfaction details for an explanation.

    This data can be verbose and is frequently not required to understand the overall response.
    Prefer using the model/attributes/explanation parts first, and only retrieve this part when
    you specifically need to inspect how constraints were satisfied.

    Uses optional 1-based inclusive line slicing via start/end.
    Returns an object with fields: part, type, start, end, total, data.

    If the Blawx server returns an unexpected response shape, the raw server response is
    preserved in `body` and mirrored in `data` for compatibility.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
        project_id=project_id,
        team_slug=team_slug,
        question_id=question_id,
        cache_key=cache_key,
        answer_index=answer_index,
        explanation_index=explanation_index,
        part_name="constraint_satisfaction",
        start=start,
        end=end,
    )


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Blawx MCP server.")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run over stdio instead of SSE/HTTP.",
    )
    return parser


def _log_loaded_tools(logger: logging.Logger) -> None:
    logger.info(
        "Loaded tools: health, team project discovery, ontology (read + read-write CRUD), "
        "facts (read + CRUD), questions (read shared + CRUD), ask/answers/explanations, "
        "legaldocs (read + CRUD), legaldocparts (read + CRUD), encoding (read-write)"
    )
    logger.info(
        "Config via env: BLAWX_BASE_URL (default https://app.blawx.dev), BLAWX_API_KEY"
    )


def main(argv: list[str] | None = None) -> None:
    args = _build_arg_parser().parse_args(argv)

    log_level = os.environ.get("BLAWX_MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )

    logger = logging.getLogger("blawx_mcp")

    if args.stdio:
        logger.info("Starting blawx-mcp MCP server (stdio)")
        _log_loaded_tools(logger)
        asyncio.run(mcp.run_stdio_async())
        return

    # SSE transport runs an HTTP server (uvicorn). We log a small banner so it's
    # obvious the server is up.
    logger.info("Starting blawx-mcp MCP server (SSE)")
    logger.info("Listening on http://%s:%s/sse", mcp.settings.host, mcp.settings.port)
    _log_loaded_tools(logger)
    logger.info(
        "Server bind via env: BLAWX_MCP_HOST (default 127.0.0.1), BLAWX_MCP_PORT (default 8765)"
    )

    asyncio.run(mcp.run_sse_async("/"))


if __name__ == "__main__":
    main()
