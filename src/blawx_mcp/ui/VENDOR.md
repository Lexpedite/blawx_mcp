# UI assets provenance and refresh

The code viewer (`blawx_view_code` / `ui://blawx/code-viewer`) is assembled at
resource-serve time by `_build_code_viewer_html()` in `server.py`, which inlines
these generated/vendored assets into `code_viewer.html` so the served resource is
fully self-contained (no network at runtime).

## `viewer-bundle.js` (generated)

Built from the **blawx_saas** repo, not authored here. It bundles the Blawx
block definitions (blocks-only `initializeBlocks()` path) plus the
`renderBlawxWorkspace()` entry point, and treats Blockly as an external global.

Source: `blawx_saas/assets/javascript/environments/viewer/viewer.js`
(webpack entry `viewer`).

Refresh after changing Blawx blocks or the viewer entry:

```bash
# in ../blawx_saas
MY_UID=$(id -u) MY_GID=$(id -g) docker compose run --rm --no-deps webpack npm run build
cp static/js/viewer-bundle.js ../blawx_mcp/src/blawx_mcp/ui/viewer-bundle.js
```

Use the production build (`npm run build`), not the dev build: dev mode wraps
modules in `eval()`, which strict MCP-host iframe CSPs block.

## `vendor/blockly/` (vendored)

Pinned Blockly runtime, loaded as globals before `viewer-bundle.js`. Version is
recorded in `vendor/blockly/VERSION.txt`.

Refresh (pin a specific version):

```bash
BV=12.5.1   # keep in sync with VERSION.txt
cd src/blawx_mcp/ui/vendor/blockly
curl -sL "https://unpkg.com/blockly@${BV}/blockly_compressed.js" -o blockly_compressed.js
curl -sL "https://unpkg.com/blockly@${BV}/blocks_compressed.js"  -o blocks_compressed.js
curl -sL "https://unpkg.com/blockly@${BV}/msg/en.js"             -o msg/en.js
echo "VERSION ${BV}" > VERSION.txt
```
