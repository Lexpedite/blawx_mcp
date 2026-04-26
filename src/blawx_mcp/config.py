from __future__ import annotations

import os
from contextvars import ContextVar, Token
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str


_settings_override: ContextVar[Settings | None] = ContextVar(
    "_settings_override", default=None
)


def get_settings() -> Settings:
    override = _settings_override.get()
    if override is not None:
        return override

    base_url = os.environ.get("BLAWX_BASE_URL", "https://app.blawx.dev").rstrip("/")
    api_key = os.environ.get("BLAWX_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Missing BLAWX_API_KEY in environment. Set it to your Blawx API key."
        )
    return Settings(
        base_url=base_url,
        api_key=api_key,
    )


def settings_context(settings: Settings) -> Token[Settings | None]:
    """Return a Token from ContextVar.set(). Caller is responsible for reset()."""
    return _settings_override.set(settings)
