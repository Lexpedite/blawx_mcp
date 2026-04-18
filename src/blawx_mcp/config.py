from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    team_slug: str


def get_settings() -> Settings:
    base_url = os.environ.get("BLAWX_BASE_URL", "https://app.blawx.dev").rstrip("/")
    api_key = os.environ.get("BLAWX_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "Missing BLAWX_API_KEY in environment. Set it to your Blawx API key."
        )
    team_slug = os.environ.get("BLAWX_TEAM_SLUG", "").strip()
    if not team_slug:
        raise RuntimeError(
            "Missing BLAWX_TEAM_SLUG in environment. Set it to your team slug."
        )

    return Settings(
        base_url=base_url,
        api_key=api_key,
        team_slug=team_slug,
    )
