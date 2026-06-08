"""Tests for the read-only Blawx code viewer MCP App (blawx_view_code)."""
from __future__ import annotations

import asyncio
import tomllib
from importlib import resources
from pathlib import Path


# A realistic Blockly workspace serialization using only registered Blawx block
# types, including the two mutator blocks (object_declaration, relationship_selector2)
# whose extraState must deserialize.
SAMPLE_WORKSPACE = {
    "blocks": {
        "languageVersion": 0,
        "blocks": [
            {
                "type": "unattributed_rule",
                "x": 30,
                "y": 30,
                "inputs": {
                    "conditions": {
                        "block": {
                            "type": "object_category",
                            "fields": {"category_name": "game"},
                            "inputs": {
                                "object": {
                                    "block": {
                                        "type": "variable",
                                        "fields": {"variable_name": "Game"},
                                    }
                                }
                            },
                        }
                    },
                    "conclusion": {
                        "block": {
                            "type": "relationship_selector2",
                            "extraState": {
                                "relationship_name": "winner",
                                "arity": 2,
                                "parameter_types": ["game", "player"],
                            },
                            "fields": {
                                "prefix": "the winner of",
                                "postfix1": "was",
                                "postfix2": "",
                            },
                            "inputs": {
                                "parameter1": {
                                    "block": {
                                        "type": "variable",
                                        "fields": {"variable_name": "Game"},
                                    }
                                },
                                "parameter2": {
                                    "block": {
                                        "type": "variable",
                                        "fields": {"variable_name": "Player"},
                                    }
                                },
                            },
                        }
                    },
                },
            },
            {
                "type": "object_declaration",
                "x": 30,
                "y": 250,
                "extraState": {"category_name": "player"},
                "fields": {"prefix": "", "object_name": "alice", "postfix": "is a player"},
            },
        ],
    }
}

_CODE_VIEWER_META = {
    "ui": {"resourceUri": "ui://blawx/code-viewer", "visibility": ["model", "app"]}
}


def test_view_code_tool_exposes_ui_metadata():
    from blawx_mcp import server

    tools = server.mcp._tool_manager._tools
    assert tools["blawx_view_code"].meta == _CODE_VIEWER_META


def test_view_code_serializes_ui_metadata_in_tools_list():
    from blawx_mcp import server

    async def run():
        return await server.mcp.list_tools()

    tools = {
        tool.name: tool.model_dump(by_alias=True, exclude_none=True)
        for tool in asyncio.run(run())
    }

    assert tools["blawx_view_code"]["_meta"] == _CODE_VIEWER_META
    # blawx_json is the only required argument.
    assert tools["blawx_view_code"]["inputSchema"]["required"] == ["blawx_json"]


def test_view_code_result_carries_meta_and_workspace():
    from blawx_mcp import server

    async def run():
        return await server.mcp.call_tool(
            "blawx_view_code",
            {"blawx_json": SAMPLE_WORKSPACE, "title": "RPS rules"},
        )

    converted = asyncio.run(run())

    assert converted.meta == _CODE_VIEWER_META
    assert converted.content == []
    assert converted.structuredContent["ok"] is True
    assert converted.structuredContent["title"] == "RPS rules"
    assert converted.structuredContent["blawx_json"] == SAMPLE_WORKSPACE


def test_view_code_rejects_non_workspace_input():
    from blawx_mcp import server

    async def run():
        return await server.mcp.call_tool(
            "blawx_view_code",
            {"blawx_json": {"not": "a workspace"}},
        )

    converted = asyncio.run(run())

    # Still carries the UI meta so the app can show the error in-frame.
    assert converted.meta == _CODE_VIEWER_META
    assert converted.structuredContent["ok"] is False
    assert "blocks" in converted.structuredContent["error"]


def test_code_viewer_resource_registered():
    from blawx_mcp import server

    resource = server.mcp._resource_manager._resources["ui://blawx/code-viewer"]

    assert resource.name == "blawx-code-viewer"
    assert resource.mime_type == "text/html;profile=mcp-app"


def test_code_viewer_resource_is_self_contained():
    from blawx_mcp import server

    async def run():
        return await server.mcp.read_resource("ui://blawx/code-viewer")

    contents = asyncio.run(run())
    assert len(contents) == 1
    html = contents[0].content

    assert contents[0].mime_type == "text/html;profile=mcp-app"
    assert "<title>Blawx Code Viewer</title>" in html

    # Every asset marker must be replaced by inlined JS...
    for marker, _ in server._VIEWER_ASSET_MARKERS:
        assert marker not in html, marker
    # ...and there must be no external <script src> (fully self-contained).
    assert "<script src" not in html.lower()

    # The Blockly runtime and the read-only viewer bundle are inlined.
    assert "Blockly.serialization" in html
    assert "defineBlocksWithJsonArray" in html
    assert "renderBlawxWorkspace" in html

    # The page reuses the MCP Apps message bridge from the answer viewer.
    assert "receiveToolResult" in html
    assert "unwrapToolResult" in html
    assert "ui/notifications/initialized" in html


def test_code_viewer_assets_packaged_and_present():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    package_data = pyproject["tool"]["setuptools"]["package-data"]["blawx_mcp"]

    assert "ui/*.js" in package_data
    assert "ui/vendor/blockly/*.js" in package_data

    ui = resources.files("blawx_mcp") / "ui"
    assert (ui / "code_viewer.html").is_file()
    assert (ui / "viewer-bundle.js").is_file()
    assert (ui / "vendor" / "blockly" / "blockly_compressed.js").is_file()
