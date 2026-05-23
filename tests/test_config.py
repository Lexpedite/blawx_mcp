"""Tests for config.py ContextVar-based settings injection."""
from __future__ import annotations

import asyncio
import inspect
import tomllib
from importlib import resources
from pathlib import Path

import pytest

from blawx_mcp.config import Settings, _settings_override, get_settings, settings_context


# ---------------------------------------------------------------------------
# Env-var path: unchanged behaviour
# ---------------------------------------------------------------------------


def test_get_settings_reads_env_vars(monkeypatch):
    monkeypatch.setenv("BLAWX_API_KEY", "test-key")
    monkeypatch.setenv("BLAWX_BASE_URL", "https://custom.blawx.dev")

    s = get_settings()

    assert s.api_key == "test-key"
    assert s.base_url == "https://custom.blawx.dev"


def test_get_settings_default_base_url(monkeypatch):
    monkeypatch.setenv("BLAWX_API_KEY", "test-key")
    monkeypatch.delenv("BLAWX_BASE_URL", raising=False)

    s = get_settings()

    assert s.base_url == "https://app.blawx.dev"


def test_get_settings_raises_on_missing_api_key(monkeypatch):
    monkeypatch.delenv("BLAWX_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="BLAWX_API_KEY"):
        get_settings()


def test_get_settings_ignores_team_slug_env_var(monkeypatch):
    monkeypatch.setenv("BLAWX_API_KEY", "test-key")
    monkeypatch.setenv("BLAWX_TEAM_SLUG", "ignored-team")

    s = get_settings()

    assert not hasattr(s, "team_slug")


# ---------------------------------------------------------------------------
# Injection: settings_context() overrides env vars
# ---------------------------------------------------------------------------


def test_settings_context_injects_settings(monkeypatch):
    # Even with env vars absent, the injected settings are returned.
    monkeypatch.delenv("BLAWX_API_KEY", raising=False)

    injected = Settings(
        base_url="https://injected.example.com",
        api_key="injected-key",
    )
    token = settings_context(injected)
    try:
        s = get_settings()
        assert s is injected
    finally:
        _settings_override.reset(token)


# ---------------------------------------------------------------------------
# No leakage: after reset(), env-var path is restored
# ---------------------------------------------------------------------------


def test_settings_context_reset_restores_env_var_path(monkeypatch):
    monkeypatch.setenv("BLAWX_API_KEY", "env-key")

    injected = Settings(
        base_url="https://injected.example.com",
        api_key="injected-key",
    )
    token = settings_context(injected)
    _settings_override.reset(token)

    s = get_settings()
    assert s.api_key == "env-key"


def test_no_context_leakage_between_async_tasks(monkeypatch):
    """An override set in one asyncio task must not bleed into another."""
    monkeypatch.setenv("BLAWX_API_KEY", "env-key")

    results: dict[str, str] = {}

    async def task_with_override():
        injected = Settings(
            base_url="https://injected.example.com",
            api_key="task-key",
        )
        token = settings_context(injected)
        try:
            await asyncio.sleep(0)  # yield to allow the other task to run
            results["with_override"] = get_settings().api_key
        finally:
            _settings_override.reset(token)

    async def task_without_override():
        await asyncio.sleep(0)  # yield so the override task runs first
        results["without_override"] = get_settings().api_key

    async def run():
        await asyncio.gather(
            asyncio.create_task(task_with_override()),
            asyncio.create_task(task_without_override()),
        )

    asyncio.run(run())

    assert results["with_override"] == "task-key"
    assert results["without_override"] == "env-key"


# ---------------------------------------------------------------------------
# Cache isolation: _resolve_team_id keyed by (api_key, team_slug)
# ---------------------------------------------------------------------------


def test_team_id_cache_isolation():
    """Different api_key values with the same team_slug must use separate cache entries."""
    from blawx_mcp.server import _TEAM_ID_CACHE

    _TEAM_ID_CACHE.clear()
    _TEAM_ID_CACHE[("key-a", "my-team")] = 1
    _TEAM_ID_CACHE[("key-b", "my-team")] = 2

    assert _TEAM_ID_CACHE[("key-a", "my-team")] == 1
    assert _TEAM_ID_CACHE[("key-b", "my-team")] == 2
    # No cross-contamination: same slug, different key → different value
    assert _TEAM_ID_CACHE[("key-a", "my-team")] != _TEAM_ID_CACHE[("key-b", "my-team")]

    _TEAM_ID_CACHE.clear()


def test_resolve_team_id_uses_team_list_response(monkeypatch):
    from blawx_mcp import server

    class FakeResponse:
        is_success = True
        status_code = 200
        headers = {"content-type": "application/json"}

        def json(self):
            return [{"id": 42, "slug": "my-team"}]

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, headers):
            return FakeResponse()

    server._TEAM_ID_CACHE.clear()
    monkeypatch.setattr(server.httpx, "AsyncClient", FakeClient)

    async def run():
        return await server._resolve_team_id(
            base_url="https://example.test",
            api_key="key",
            team_slug="my-team",
        )

    assert asyncio.run(run()) == 42
    server._TEAM_ID_CACHE.clear()


def test_request_json_returns_compact_response(monkeypatch):
    from blawx_mcp import server

    class FakeResponse:
        status_code = 204
        is_success = True
        headers = {"content-type": "application/json", "location": "/unused"}

        def json(self):
            return {}

    class FakeClient:
        def __init__(self, timeout):
            self.timeout = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def request(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(server.httpx, "AsyncClient", FakeClient)

    async def run():
        return await server._request_json(
            method="PUT",
            url="https://example.test/api",
            api_key="key",
            json_body={"large": "request"},
            params={"debug": "nope"},
        )

    result = asyncio.run(run())

    assert result == {"status_code": 204, "ok": True, "body": {}}


def test_project_scoped_tools_require_team_slug():
    """Project-scoped public tools should expose team_slug explicitly."""
    from blawx_mcp import server

    excluded = {"blawx_health", "blawx_encoding_guide", "blawx_teams_list"}
    for name, func in vars(server).items():
        if not name.startswith("blawx_") or name in excluded:
            continue

        signature = inspect.signature(func)
        if "project_id" in signature.parameters:
            assert "team_slug" in signature.parameters, name


def test_discovery_tool_signatures():
    from blawx_mcp import server

    teams_signature = inspect.signature(server.blawx_teams_list)
    projects_signature = inspect.signature(server.blawx_projects_list)
    declared_objects_signature = inspect.signature(server.blawx_declared_objects_list)

    assert "team_slug" not in teams_signature.parameters
    assert list(projects_signature.parameters) == ["team_slug"]
    assert list(declared_objects_signature.parameters) == ["team_slug", "project_id"]
    assert not hasattr(server, "blawx_project_detail")


def test_removed_redundant_ontology_parameter_read_tools():
    from blawx_mcp import server

    assert not hasattr(server, "blawx_ontology_categories_list")
    assert not hasattr(server, "blawx_ontology_relationships_list")
    assert not hasattr(server, "blawx_ontology_relationship_parameters_list")
    assert not hasattr(server, "blawx_ontology_relationship_parameter_detail")


def test_settings_has_no_team_slug():
    signature = inspect.signature(Settings)

    assert "team_slug" not in signature.parameters


def test_mcp_tools_keep_structured_output_schemas():
    from blawx_mcp import server

    for name, tool in server.mcp._tool_manager._tools.items():
        if name in {"blawx_encoding_guide", "blawx_legaldocparts_list"}:
            assert tool.fn_metadata.output_schema is None, name
        else:
            assert tool.fn_metadata.output_schema is not None, name


def test_ask_tools_expose_answer_viewer_ui_metadata():
    from blawx_mcp import server

    expected = {"ui": {"resourceUri": "ui://blawx/answers", "visibility": ["model", "app"]}}

    assert server.mcp._tool_manager._tools["blawx_question_ask_with_fact_scenario"].meta == expected
    assert server.mcp._tool_manager._tools["blawx_question_ask_with_facts"].meta == expected


def test_ask_tools_serialize_answer_viewer_ui_metadata_in_tools_list():
    from blawx_mcp import server

    async def run():
        return await server.mcp.list_tools()

    tools = {tool.name: tool.model_dump(by_alias=True, exclude_none=True) for tool in asyncio.run(run())}
    expected = {"ui": {"resourceUri": "ui://blawx/answers", "visibility": ["model", "app"]}}

    assert tools["blawx_question_ask_with_fact_scenario"]["_meta"] == expected
    assert tools["blawx_question_ask_with_facts"]["_meta"] == expected


def test_ask_tool_result_exposes_ui_meta_without_resource_link(monkeypatch):
    from blawx_mcp import server

    async def fake_project_request_body(**kwargs):
        return {
            "status_code": 200,
            "ok": True,
            "body": {
                "cache_key": "cache-123",
                "ttl_seconds": 60,
                "created_at": "2026-05-23T12:00:00Z",
                "answer_count": 2,
            },
        }

    monkeypatch.setattr(server, "_project_request_body", fake_project_request_body)

    async def run():
        return await server.mcp.call_tool(
            "blawx_question_ask_with_fact_scenario",
            {"team_slug": "team", "project_id": 1, "question_id": 2, "fact_scenario_id": 3},
        )

    converted = asyncio.run(run())

    assert converted.meta == {"ui": {"resourceUri": "ui://blawx/answers", "visibility": ["model", "app"]}}
    assert converted.structuredContent["cache_key"] == "cache-123"
    assert len(converted.content) == 1
    assert converted.content[0].type == "text"
    assert '"cache_key": "cache-123"' in converted.content[0].text


def test_answer_viewer_resource_registered():
    from blawx_mcp import server

    resource = server.mcp._resource_manager._resources["ui://blawx/answers"]

    assert resource.name == "blawx-answer-viewer"
    assert resource.mime_type == "text/html;profile=mcp-app"


def test_answer_viewer_resource_returns_html():
    from blawx_mcp import server

    async def run():
        return await server.mcp.read_resource("ui://blawx/answers")

    contents = asyncio.run(run())

    assert len(contents) == 1
    assert contents[0].mime_type == "text/html;profile=mcp-app"
    assert "<title>Blawx Answers</title>" in contents[0].content
    assert "receiveToolResult" in contents[0].content
    assert "loadExplanations" in contents[0].content
    assert "loadPart" in contents[0].content


def test_answer_viewer_packaged_as_package_data():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    package_data = pyproject["tool"]["setuptools"]["package-data"]["blawx_mcp"]
    ui_path = resources.files("blawx_mcp") / "ui" / "answer_viewer.html"

    assert "ui/*.html" in package_data
    assert ui_path.is_file()


def test_encoding_guide_returns_content_only():
    from blawx_mcp import server

    async def run():
        return await server.mcp.call_tool("blawx_encoding_guide", {"topic": "ontology"})

    converted = asyncio.run(run())

    assert isinstance(converted, list)
    assert len(converted) == 1
    assert "# Blawx ontology guidance" in converted[0].text


def test_legaldocparts_list_returns_markdown_content_only(monkeypatch):
    from blawx_mcp import server

    markdown = (
        "Legend: each item is `- <legaldocpart_id> [<encodingpart_id> <marker>] <index> <text>`.\n\n"
        "- 10 20 ! Section text\n"
    )

    async def fake_project_request_json(**kwargs):
        return {"status_code": 200, "ok": True, "body": markdown}

    monkeypatch.setattr(server, "_project_request_json", fake_project_request_json)

    async def run():
        return await server.mcp.call_tool(
            "blawx_legaldocparts_list",
            {"team_slug": "team", "project_id": 1, "legal_doc_id": 2},
        )

    converted = asyncio.run(run())

    assert isinstance(converted, list)
    assert len(converted) == 1
    assert converted[0].text == markdown


def test_structured_tools_use_fastmcp_default_duplicate_output():
    from blawx_mcp import server

    tool = server.mcp._tool_manager._tools["blawx_health"]

    converted = tool.fn_metadata.convert_result({"ok": True})

    assert isinstance(converted, tuple)
    content, structured = converted
    assert len(content) == 1
    assert '"ok"' in content[0].text
    assert structured["ok"] is True


def test_encoding_guide_list_and_quickstart_topics():
    from blawx_mcp import server

    async def run(topic):
        return await server.mcp.call_tool("blawx_encoding_guide", {"topic": topic})

    listed = asyncio.run(run("list"))[0].text
    quickstart = asyncio.run(run("quickstart"))[0].text
    default = asyncio.run(server.mcp.call_tool("blawx_encoding_guide", {}))[0].text

    assert "# Guide Topics" in listed
    assert "`ontology`:" in listed
    assert "# Guide Topics" in quickstart
    assert "First call `blawx_teams_list`" in default
    assert "# Guide Topics" in default


def test_encoding_guide_invalid_topic_points_to_quickstart_or_list():
    from blawx_mcp import server

    async def run():
        return await server.mcp.call_tool("blawx_encoding_guide", {"topic": "bogus"})

    converted = asyncio.run(run())

    assert "Unknown guide topic `bogus`" in converted[0].text
    assert "quickstart" in converted[0].text
    assert "list" in converted[0].text
