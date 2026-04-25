# ADR 0001: Use `contextvars.ContextVar` for Per-Request Settings Injection

## Status

Accepted

## Context

`blawx_mcp` is used both as a local CLI/server tool (single-user, settings from environment
variables) and as an embeddable library in hosted multi-tenant server environments (many
concurrent users, each with their own Blawx API key and team slug).

In the original implementation, `get_settings()` always read configuration from environment
variables and `_TEAM_ID_CACHE` used only `team_slug` as a key. This design works for
single-user local use but makes it impossible to safely support concurrent requests from
different users because:

- There is no way to inject per-request settings; all concurrent requests share the same
  environment variables.
- The `team_slug`-only cache key risks returning a cached team ID for one user when a
  different user with the same slug but a different API key makes a request.

## Decision

1. **`ContextVar`-based settings override**: A module-level
   `ContextVar[Settings | None]` named `_settings_override` is added to `config.py`.
   `get_settings()` checks this variable first; if it holds a `Settings` instance the
   function returns it immediately, skipping the environment-variable path entirely.

2. **`settings_context()` helper**: A new public function `settings_context(settings)`
   calls `_settings_override.set(settings)` and returns the resulting `Token`. Callers
   are responsible for calling `_settings_override.reset(token)` when the request
   context ends (e.g., in a `finally` block).

3. **`(api_key, team_slug)` cache key**: `_TEAM_ID_CACHE` in `server.py` is changed from
   `dict[str, int]` to `dict[tuple[str, str], int]`. The cache key is now the pair
   `(api_key, team_slug)`, which prevents one user's cached team ID from being returned
   to a different user who happens to share the same team slug.

## Rationale

Python's `contextvars` module was designed specifically for this pattern. Each `asyncio`
task inherits a *copy* of the current context at creation time. Any `ContextVar.set()`
call inside that task affects only that task's copy, so two concurrently executing async
tasks can hold different settings values without interfering with each other. This is the
standard mechanism for request-scoped state in async frameworks such as `Starlette` and
`FastAPI`.

`contextvars` requires no external dependencies, introduces no thread-safety concerns, and
adds no overhead for the existing single-user path (the `ContextVar.get()` call is
effectively a dictionary lookup that returns `None` and falls through immediately).

## Consequences

- **No breaking changes.** Local CLI users and single-user SSE deployments see identical
  behaviour. `get_settings()` is still called in exactly the same three places inside
  `server.py` with no changes to those call sites.
- **Hosted consumers** inject per-request settings by calling `settings_context()` before
  dispatching MCP tool calls and reset the override in a `finally` block:

  ```python
  from blawx_mcp import Settings, settings_context
  from blawx_mcp.config import _settings_override

  settings = Settings(
      base_url="https://app.blawx.dev",
      api_key="my-key",
      team_slug="my-team",
  )
  token = settings_context(settings)
  try:
      # ... invoke MCP tools in this async context ...
      pass
  finally:
      _settings_override.reset(token)
  ```

- **Cache isolation** is guaranteed per `(api_key, team_slug)` pair, eliminating any
  possibility of cross-user cache collisions even when different users share an identical
  team slug.

## References

- [Python `contextvars` documentation](https://docs.python.org/3/library/contextvars.html)
