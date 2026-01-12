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
from .schemas import AskFactsPayload

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
async def blawx_questions_list() -> dict[str, Any]:
    """List available questions.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/shared/"
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
async def blawx_question_ask_with_fact_scenario(
    question_id: int, fact_scenario_id: int
) -> dict[str, Any]:
    """Ask a question (using id from blawx_questions_list) using a stored
    fact scenario (using id from blawx_fact_scenarios_list).
    """
    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/ask/qfa/"
    )
    payload = {"facts": fact_scenario_id}
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        params={"output_styles": ["human"]},
        json_body=payload,
        timeout_seconds=120.0,
    )


@mcp.tool()
async def blawx_question_ask_with_facts(question_id: int, facts: AskFactsPayload) -> dict[str, Any]:
    """Ask a question (using id from blawx_questions_list)
    using a structured facts payload.

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
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        params={"output_styles": ["human"]},
        json_body=payload,
        timeout_seconds=120.0,
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
        "Loaded tools: blawx_health, blawx_ontology_list, blawx_ontology_category_detail, "
        "blawx_ontology_relationship_detail, blawx_fact_scenarios_list, blawx_fact_scenario_detail, "
        "blawx_shared_questions_list, blawx_shared_question_detail, "
        "blawx_question_ask_with_fact_scenario, blawx_question_ask_with_facts"
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
