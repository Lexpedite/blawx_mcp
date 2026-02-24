"""Human guidance exposed via MCP resources/prompts.

These are intentionally written as standalone markdown snippets so that:
- agents that support MCP resources can fetch and read them, and
- agents that only use tool descriptions still get the essentials via tool docstrings.
"""

from pathlib import Path


def _read_md_guide(filename: str) -> str:
   path = Path(__file__).resolve().parent / "md_guides" / filename
   try:
      return path.read_text(encoding="utf-8")
   except FileNotFoundError:
      return f"# Missing guide\n\nCould not find `{filename}` in `md_guides`."

SCA_SP_GUIDE_MD = _read_md_guide("scasp.md")
ONTOLOGY_GUIDE_MD = _read_md_guide("ontology.md")
BLAWX_JSON_GUIDE_MD = _read_md_guide("blawx_json.md")
ENCODINGPART_GUIDE_MD = _read_md_guide("encodingpart.md")
ENCODING_EXAMPLES_GUIDE_MD = _read_md_guide("encoding_examples.md")
BLAWX_BLOCKS_GUIDE_MD = _read_md_guide("blawx_blocks.md")
VALID_BLAWX_JSON_GUIDE_MD = _read_md_guide("valid_blawx_json.md")
