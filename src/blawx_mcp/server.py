from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from .config import get_settings


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


@mcp.tool()
async def blawx_health() -> dict[str, Any]:
    """Check Blawx app health endpoint using Api-Key auth.

    Calls `GET {BLAWX_BASE_URL}/health` with `Authorization: Api-Key <BLAWX_API_KEY>`.
    """
    settings = get_settings()
    url = f"{settings.base_url}/health"

    headers = {
        "Authorization": f"Api-Key {settings.api_key}",
        "Accept": "application/json, text/plain;q=0.9, */*;q=0.8",
    }

    timeout = httpx.Timeout(10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=headers)

    body = await _get_json_or_text(resp)
    return {
        "url": url,
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


@mcp.tool()
async def blawx_lexpedite_project6_question7_ask(facts: int = 32) -> dict[str, Any]:
    """Call Blawx lexpedite ask endpoint.

    POSTs to `/a/lexpedite/project/42/questions/59/ask/qfa/` with JSON body `{"facts": <facts>}`.
    """
    settings = get_settings()
    url = f"{settings.base_url}/a/lexpedite/project/42/questions/59/ask/qfa/"

    headers = {
        "Authorization": f"Api-Key {settings.api_key}",
        "Accept": "application/json, text/plain;q=0.9, */*;q=0.8",
    }

    payload = {"facts": facts}
    timeout = httpx.Timeout(30.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=headers, json=payload)

    body = await _get_json_or_text(resp)
    return {
        "url": url,
        "request": payload,
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
    logger.info("Loaded tools: blawx_health, blawx_lexpedite_project6_question7_ask")
    logger.info(
        "Config via env: BLAWX_BASE_URL (default https://app.blawx.dev), BLAWX_API_KEY (required for API calls)"
    )
    logger.info(
        "Server bind via env: BLAWX_MCP_HOST (default 127.0.0.1), BLAWX_MCP_PORT (default 8765)"
    )

    asyncio.run(mcp.run_sse_async("/"))


if __name__ == "__main__":
    main()
