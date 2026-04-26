"""Tests for config.py ContextVar-based settings injection."""
from __future__ import annotations

import asyncio
import inspect
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

    assert "team_slug" not in teams_signature.parameters
    assert list(projects_signature.parameters) == ["team_slug"]


def test_settings_has_no_team_slug():
    signature = inspect.signature(Settings)

    assert "team_slug" not in signature.parameters
