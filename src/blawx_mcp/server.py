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
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    headers = _auth_headers(api_key)
    timeout = httpx.Timeout(timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, url, headers=headers, json=json_body)

    body = await _get_json_or_text(resp)
    return {
        "url": url,
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
    """Check Blawx app health endpoint using Api-Key auth.

    Calls `GET {BLAWX_BASE_URL}/health/` with `Authorization: Api-Key <BLAWX_API_KEY>`.
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
    """List ontology for the configured team/project.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/ontology/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_category_detail(category_id: int) -> dict[str, Any]:
    """Get a specific ontology category by id.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/ontology/categories/{category_id}/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/categories/{category_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_ontology_relationship_detail(relationship_id: int) -> dict[str, Any]:
    """Get a specific ontology relationship by id.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/ontology/relationships/{relationship_id}/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/ontology/relationships/{relationship_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_fact_scenarios_list() -> dict[str, Any]:
    """List available fact scenarios (fact patterns) for the configured team/project.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/facts/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_fact_scenario_detail(fact_scenario_id: int) -> dict[str, Any]:
    """Get details for a specific fact scenario (fact pattern) by id.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/facts/{fact_scenario_id}/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/facts/{fact_scenario_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_shared_questions_list() -> dict[str, Any]:
    """List shared questions available in the configured team/project.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/questions/shared/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/shared/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_shared_question_detail(question_id: int) -> dict[str, Any]:
    """Get details for a specific shared question.

    Calls `GET /api/teams/{team_id}/projects/{project_id}/questions/shared/{question_id}/`.
    """
    settings = get_settings()
    team_id = await _resolve_team_id(
        base_url=settings.base_url, api_key=settings.api_key, team_slug=settings.team_slug
    )
    url = f"{settings.base_url}/api/teams/{team_id}/projects/{settings.project_id}/questions/shared/{question_id}/"
    return await _request_json(method="GET", url=url, api_key=settings.api_key, timeout_seconds=30.0)


@mcp.tool()
async def blawx_question_ask_with_fact_scenario(
    question_id: int, fact_scenario_id: int = 32
) -> dict[str, Any]:
    """Ask a question using a stored fact scenario (fact pattern).

    Calls `POST /a/{team_slug}/project/{proj}/questions/{question}/ask/qfa/` with JSON body
    `{"facts": <fact_scenario_id>}`.
    """
    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/ask/qfa/"
    )
    payload = {"facts": fact_scenario_id}
    return await _request_json(
        method="POST", url=url, api_key=settings.api_key, json_body=payload, timeout_seconds=60.0
    )


@mcp.tool()
async def blawx_question_ask_with_facts(question_id: int, facts: AskFactsPayload) -> dict[str, Any]:
    """Ask a question using a structured facts payload.

    Calls `POST /a/{team_slug}/project/{proj}/questions/{question}/ask/`.

    The request body is a top-level JSON array of facts; the `facts` parameter is validated
    against the Pydantic schema in `blawx_mcp.schemas`.
    """
    settings = get_settings()
    url = (
        f"{settings.base_url}/a/{settings.team_slug}/project/{settings.project_id}"
        f"/questions/{question_id}/ask/"
    )

    # The underlying endpoint expects the raw list payload, not a wrapper object.
    payload = facts.root
    return await _request_json(
        method="POST",
        url=url,
        api_key=settings.api_key,
        json_body=payload,
        timeout_seconds=60.0,
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
