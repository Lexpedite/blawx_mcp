from __future__ import annotations

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
    BLAWX_JSON_GUIDE_MD,
    ENCODINGPART_GUIDE_MD,
    ONTOLOGY_GUIDE_MD,
    SCA_SP_GUIDE_MD,
)
from .schemas import AskFactsPayload, EncodingPartUpdatePayload

_TEAM_ID_CACHE: dict[str, int] = {}


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
    """Read this first before editing encoding parts.

    Use this tool before `blawx_encodingpart_update` to learn:
    - required request shape (`blawx_json` key only)
    - Blawx JSON formatting expectations
    - suggested encoding workflow

    Topics: quickstart | blawx-json | encodingpart | ontology | scasp | all
    """

    normalized = topic.strip().lower()
    guides = {
        "scasp": SCA_SP_GUIDE_MD,
        "ontology": ONTOLOGY_GUIDE_MD,
        "blawx-json": BLAWX_JSON_GUIDE_MD,
        "encodingpart": ENCODINGPART_GUIDE_MD,
    }

    quickstart = (
        "Use `blawx_encodingpart_get` to inspect current encoding first.\n"
        "When writing, call `blawx_encodingpart_update` with only this shape:\n"
        "`{\"blawx_json\": <json object>}`\n"
        "Do not send `content`, `scasp_encoding`, or stringified JSON.\n"
        "Read `blawx-json` and `encodingpart` topics before generating payloads."
    )

    if normalized == "quickstart":
        selected = quickstart
    elif normalized == "all":
        selected = (
            "# Quickstart\n"
            f"{quickstart}\n\n"
            "# EncodingPart Workflow\n"
            f"{ENCODINGPART_GUIDE_MD}\n\n"
            "# Blawx JSON Blocks\n"
            f"{BLAWX_JSON_GUIDE_MD}\n\n"
            "# Ontology\n"
            f"{ONTOLOGY_GUIDE_MD}\n\n"
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
            "available_topics": ["quickstart", "blawx-json", "encodingpart", "ontology", "scasp", "all"],
        }

    return {
        "ok": True,
        "topic": normalized,
        "guidance_markdown": selected,
        "available_topics": ["quickstart", "blawx-json", "encodingpart", "ontology", "scasp", "all"],
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
    cached = _TEAM_ID_CACHE.get(team_slug)
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
                    _TEAM_ID_CACHE[team_slug] = team_id
                    return team_id

            next_url = data.get("next")
            if not next_url:
                break
            url = next_url

    raise RuntimeError(
        f"Team slug {team_slug!r} not found in /teams/api/teams/ results for this API key."
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
async def blawx_ontology_list() -> dict[str, Any]:
    """List ontology (available categories and relationships).
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_categories_list() -> dict[str, Any]:
    """List ontology categories.

    This endpoint is read-write in the API (create/update/delete are also supported).
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/categories/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_category_create(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new ontology category.

    The request schema depends on the server; pass the JSON body as a dict.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/categories/"
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_category_update(category_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace an ontology category (PUT)."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/categories/{category_id}/"
    )
    return await _request_json(
        method="PUT",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_category_delete(category_id: int) -> dict[str, Any]:
    """Delete an ontology category."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/categories/{category_id}/"
    )
    return await _request_json(method="DELETE", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_category_detail(category_id: int) -> dict[str, Any]:
    """Get category details by id obtained from blawx_ontology_list tool.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/categories/{category_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationship_detail(relationship_id: int) -> dict[str, Any]:
    """Get relationship details by id obtained from blawx_ontology_list tool.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/relationships/{relationship_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationships_list() -> dict[str, Any]:
    """List ontology relationships."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/relationships/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationship_create(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new ontology relationship."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/relationships/"
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_update(relationship_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace an ontology relationship (PUT)."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/"
    )
    return await _request_json(
        method="PUT",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_delete(relationship_id: int) -> dict[str, Any]:
    """Delete an ontology relationship."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/"
    )
    return await _request_json(method="DELETE", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationship_parameters_list(relationship_id: int) -> dict[str, Any]:
    """List parameters for a relationship."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/parameters/"
    )
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationship_parameter_create(relationship_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new relationship parameter definition."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/parameters/"
    )
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameter_update(
    relationship_id: int, parameter_id: int, payload: dict[str, Any]
) -> dict[str, Any]:
    """Replace a relationship parameter definition (PUT)."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/parameters/{parameter_id}/"
    )
    return await _request_json(
        method="PUT",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_ontology_relationship_parameter_detail(relationship_id: int, parameter_id: int) -> dict[str, Any]:
    """Get a relationship parameter definition by id."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/parameters/{parameter_id}/"
    )
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationship_parameter_delete(relationship_id: int, parameter_id: int) -> dict[str, Any]:
    """Delete a relationship parameter definition."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/ontology/relationships/{relationship_id}/parameters/{parameter_id}/"
    )
    return await _request_json(method="DELETE", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_fact_scenarios_list() -> dict[str, Any]:
    """List available fact scenarios for use in the blawx_ask_question_with_fact_scenario tool.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_fact_scenario_create(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new fact scenario.

    The request schema depends on the server; pass the JSON body as a dict.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/"
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_fact_scenario_detail(fact_scenario_id: int) -> dict[str, Any]:
    """Get fact scenario details by id obtained from blawx_fact_scenarios_list tool.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/{fact_scenario_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_fact_scenario_update(fact_scenario_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace a fact scenario (PUT)."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/{fact_scenario_id}/"
    return await _request_json(
        method="PUT",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_fact_scenario_delete(fact_scenario_id: int) -> dict[str, Any]:
    """Delete a fact scenario."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/{fact_scenario_id}/"
    return await _request_json(method="DELETE", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_questions_list() -> dict[str, Any]:
    """List available shared questions (read-only).

    For read-write question management, use blawx_questions_list_all and related tools.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/shared/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_questions_list_all() -> dict[str, Any]:
    """List all questions in the project (read-write collection)."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_question_detail(question_id: int) -> dict[str, Any]:
    """Get question by id obtained from blawx_questions_list tool.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/shared/{question_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_question_detail_all(question_id: int) -> dict[str, Any]:
    """Get a question from the read-write questions endpoint by id."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/{question_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_question_create(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a new question in the project."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/"
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_question_update(question_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Replace a question (PUT)."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/{question_id}/"
    return await _request_json(
        method="PUT",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=30.0,
    )


@mcp.tool()
async def blawx_question_delete(question_id: int) -> dict[str, Any]:
    """Delete a question."""

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/{question_id}/"
    return await _request_json(method="DELETE", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_question_ask_with_fact_scenario(question_id: int, fact_scenario_id: int) -> dict[str, Any]:
    """Ask a question using a stored fact scenario.

        Returns a cache key for later retrieval.

        Notes:
            - The returned results are temporary. When available, `ttl_seconds` indicates how long
                the cached response is expected to remain available.
            - If follow-up retrieval tools return `status_code` 410 (expired / not found), re-run
                this tool (or `blawx_question_ask_with_facts`) to obtain a fresh cache key.
    """
    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/ask/qfa/"
    )
    payload = {"facts": fact_scenario_id}
    resp = await _request_body(
        method="POST",
        url=url,
        api_key=settings.api_key,
        params={"output_styles": ["human"], "cached": True},
        json_body=payload,
        timeout_seconds=120.0,
    )

    body = resp.get("body")
    cache_key = _extract_cache_key(body)
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "cache_key": cache_key,
        "ttl_seconds": _extract_optional_int(body, "ttl_seconds"),
        "created_at": _extract_optional_str(body, "created_at"),
        "answer_count": _extract_optional_int(body, "answer_count"),
    }


@mcp.tool()
async def blawx_question_ask_with_facts(question_id: int, facts: AskFactsPayload) -> dict[str, Any]:
    """Ask a question using a structured facts payload.

        Returns a cache key for later retrieval.

        Notes:
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
        - Object names must be lowercase strings without spaces (e.g., "john_doe", "contract_123", "department_of_defence")
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
    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/ask/"
    )

    # The underlying endpoint expects the raw list payload, not a wrapper object.
    # `facts.root` contains Pydantic models; dump them to plain JSON-serializable dicts.
    payload = [fact.model_dump(exclude_none=True) for fact in facts.root]
    resp = await _request_body(
        method="POST",
        url=url,
        api_key=settings.api_key,
        params={"output_styles": ["human"], "cached": True},
        json_body=payload,
        timeout_seconds=120.0,
    )

    body = resp.get("body")
    cache_key = _extract_cache_key(body)
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "cache_key": cache_key,
        "ttl_seconds": _extract_optional_int(body, "ttl_seconds"),
        "created_at": _extract_optional_str(body, "created_at"),
        "answer_count": _extract_optional_int(body, "answer_count"),
    }


@mcp.tool()
async def blawx_list_answers(question_id: int, cache_key: str) -> dict[str, Any]:
    """List answers for a previously asked question.

        Returns:
            - total: total number of answers
            - answers: list of {answer_index, bindings, explanation_count}

        If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/responses/{cache_key}/answers/"
    )
    resp = await _request_body(
        method="GET",
        url=url,
        api_key=settings.api_key,
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
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "total": len(answer_indices),
        "answers": [{"answer_index": i, "bindings": "", "explanation_count": 0} for i in answer_indices],
        "note": "Unexpected response shape; returned inferred indices only",
    }


@mcp.tool()
async def blawx_cached_response_meta(question_id: int, cache_key: str) -> dict[str, Any]:
    """Retrieve cached-response metadata (ttl, created time, answer count when available).

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/responses/{cache_key}/"
    )
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_list_explanations(question_id: int, cache_key: str, answer_index: int) -> dict[str, Any]:
    """List explanations available for a specific answer.

        Returns:
            - answer_index
            - bindings
            - explanations: list of {explanation_index, parts_available}

        Important:
            - The explanation text can include variables whose meaning depends on constraints.
                Always retrieve the attributes part for the same explanation when interpreting the
                explanation part; otherwise conclusions may be incorrect.

        If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/responses/{cache_key}/answers/{answer_index}/"
    )
    resp = await _request_body(
        method="GET",
        url=url,
        api_key=settings.api_key,
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
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "answer_index": answer_index,
        "bindings": "",
        "explanations": [{"explanation_index": i, "parts_available": []} for i in explanation_indices],
        "note": "Unexpected response shape; returned inferred indices only",
    }


@mcp.tool()
async def blawx_get_explanation_full(
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
) -> dict[str, Any]:
    """Get the full explanation object (all parts, unsliced).

    This can be large; prefer blawx_get_*_part tools when you only need one section.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/responses/{cache_key}/answers/{answer_index}"
        f"/explanations/{explanation_index}/"
    )
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=60.0)


@mcp.tool()
async def blawx_legaldocs_list() -> dict[str, Any]:
    """List legal docs in the project.

    This returns document-level metadata. To read legislation text, then call:
    1) `blawx_legaldocparts_list` for the chosen legal doc
    2) `blawx_legaldocpart_detail` for each relevant part

    Note: This MCP server currently does not expose tools to create/update/delete legaldocs.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/legaldocs/"
    result = await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)
    return {
        **result,
        "workflow_hint": (
            "This is a document list. To read legal text, call blawx_legaldocparts_list "
            "for a legal_doc_id, then call blawx_legaldocpart_detail for the relevant part(s)."
        ),
        "next_recommended_tool": "blawx_legaldocparts_list",
    }


@mcp.tool()
async def blawx_legaldoc_detail(legal_doc_id: int) -> dict[str, Any]:
    """Get a legal doc by id.

    This returns document-level metadata. To read the legislative text itself,
    list parts with `blawx_legaldocparts_list` and then fetch part text with
    `blawx_legaldocpart_detail`.

    Note: This MCP server currently does not expose tools to create/update/delete legaldocs.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/legaldocs/{legal_doc_id}/"
    result = await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)
    return {
        **result,
        "workflow_hint": (
            "This is legal-doc metadata. To read legal text, call blawx_legaldocparts_list "
            "for this legal_doc_id, then call blawx_legaldocpart_detail for relevant part ids."
        ),
        "next_recommended_tool": "blawx_legaldocparts_list",
    }


@mcp.tool()
async def blawx_legaldocparts_list(legal_doc_id: int) -> dict[str, Any]:
    """List parts for a legal doc.

    This list is mainly navigational metadata (part ids/titles/order). To view the
    actual legislation text for a part, call `blawx_legaldocpart_detail` for that part id.

    Note: This MCP server currently does not expose tools to create/update/delete legaldocparts.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/legaldocs/{legal_doc_id}/parts/"
    )
    result = await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)
    return {
        **result,
        "workflow_hint": (
            "This is a parts list. To read the actual text, call blawx_legaldocpart_detail "
            "for each relevant legal_doc_part_id."
        ),
        "next_recommended_tool": "blawx_legaldocpart_detail",
    }


@mcp.tool()
async def blawx_legaldocpart_detail(legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Get a single legal doc part by id.

    Use this tool to view the actual text/content for a legal doc part.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/"
    )
    result = await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)
    return {
        **result,
        "workflow_hint": "This tool returns the part detail, including the legal text/content when present.",
    }


@mcp.tool()
async def blawx_encodingpart_get(legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Get the encoding for a specific legal doc part.

    Use `blawx_encoding_guide` first (topic: quickstart, then blawx-json/encodingpart)
    before creating or editing encoding payloads.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/encoding/"
    )
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_encodingpart_update(
    legal_doc_id: int, legal_doc_part_id: int, payload: EncodingPartUpdatePayload
) -> dict[str, Any]:
    """Replace the encoding for a legal doc part (PUT).

    Read `blawx_encoding_guide` first. This tool accepts only this payload shape:
    {"blawx_json": <json object>}

    Do not send `content`, `scasp_encoding`, or stringified JSON.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/encoding/"
    )
    return await _request_json(
        method="PUT",
        url=url,
        api_key=settings.api_key,
        json_body=payload.model_dump(),
        timeout_seconds=60.0,
    )


@mcp.tool()
async def blawx_encodingpart_delete(legal_doc_id: int, legal_doc_part_id: int) -> dict[str, Any]:
    """Delete the encoding for a legal doc part.

    Use `blawx_encoding_guide` if you need to recreate the encoding with the correct payload shape.
    """

    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = (
        f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}"
        f"/legaldocs/{legal_doc_id}/parts/{legal_doc_part_id}/encoding/"
    )
    return await _request_json(method="DELETE", url=url, api_key=settings.api_key, timeout_seconds=60.0)


async def _get_part(
    *,
    question_id: int,
    cache_key: str,
    answer_index: int,
    explanation_index: int,
    part_name: str,
    start: int | None,
    end: int | None,
) -> dict[str, Any]:
    settings = get_settings()
    _validate_slice(start, end)
    params: dict[str, Any] = {}
    if start is not None:
        params["start"] = start
    if end is not None:
        params["end"] = end

    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/responses/{cache_key}/answers/{answer_index}"
        f"/explanations/{explanation_index}/{part_name}/"
    )
    resp = await _request_body(
        method="GET",
        url=url,
        api_key=settings.api_key,
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
    return {
        "ok": resp["ok"],
        "status_code": resp["status_code"],
        "part": _public_part_name(part_name),
        "type": None,
        "start": start,
        "end": end,
        "total": None,
        "data": body,
        "note": "Unexpected response shape; returned body as data",
    }


@mcp.tool()
async def blawx_get_model_part(
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

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
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

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
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

        Important:
            - Always review the attributes part for the same explanation. The explanation text can
                include variables whose meaning depends on attribute constraints (or lack of constraints).
                Reading the explanation without attributes can lead to incorrect interpretation.

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
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

    If `status_code` is 410, the cache key has expired and you must re-run an ask tool.
    """

    return await _get_part(
        question_id=question_id,
        cache_key=cache_key,
        answer_index=answer_index,
        explanation_index=explanation_index,
        part_name="constraint_satisfaction",
        start=start,
        end=end,
    )


def main() -> None:
    # SSE transport runs an HTTP server (uvicorn). We log a small banner so it's
    # obvious the server is up.
    log_level = os.environ.get("BLAWX_MCP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        stream=sys.stderr,
        format="%(levelname)s %(name)s: %(message)s",
    )

    logger = logging.getLogger("blawx_mcp")
    logger.info("Starting blawx-mcp MCP server (SSE)")
    logger.info("Listening on http://%s:%s/sse", mcp.settings.host, mcp.settings.port)
    logger.info(
        "Loaded tools: health, ontology (read + read-write CRUD), facts (read + CRUD), "
        "questions (read shared + CRUD), ask/answers/explanations, legaldocs (read), encoding (read-write)"
    )
    logger.info(
        "Config via env: BLAWX_BASE_URL (default https://app.blawx.dev), BLAWX_API_KEY, BLAWX_TEAM_SLUG, BLAWX_PROJECT_ID"
    )
    logger.info(
        "Server bind via env: BLAWX_MCP_HOST (default 127.0.0.1), BLAWX_MCP_PORT (default 8765)"
    )

    asyncio.run(mcp.run_sse_async("/"))


if __name__ == "__main__":
    main()
