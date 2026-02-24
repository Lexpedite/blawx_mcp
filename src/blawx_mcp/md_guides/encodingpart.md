# EncodingParts in Blawx

An EncodingPart represents the code encoding of a specific legal-text segment.

Typical agent flow:

1. Fetch legal docs with `blawx_legaldocs_list` and pick the target `legal_doc_id`.
2. Fetch parts via `blawx_legaldocparts_list`.
3. Fetch the actual legal text/content for each relevant part with `blawx_legaldocpart_detail`.
4. Fetch ontology + examples if available.
5. Generate a suggested encoding (s(CASP) or Blawx JSON) following the guides.
6. Write back via the encoding tools:
   - `blawx_encodingpart_update` (PUT)
   - `blawx_encodingpart_patch` (PATCH)

Important: `blawx_legaldocparts_list` is primarily navigational metadata (ids/titles/order).
Use `blawx_legaldocpart_detail` to read the text of a specific legal doc part.

## Important: what the write tools accept

The MCP write tools for encoding parts intentionally accept **only the Blawx JSON blocks** encoding.

- Provide the JSON blocks structure (as JSON, not a string).
- Do **not** provide s(CASP) text/code in the write tools.
- Blawx should (re)calculate the s(CASP) encoding automatically when the JSON changes.

This MCP server intentionally does **not** expose tools to create/update legal docs or legal doc parts yet.
