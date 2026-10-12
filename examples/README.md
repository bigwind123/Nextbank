# Public Python examples

These small examples are fictional, local demonstrations of selected engineering controls. They do not call the bank's services, use credentials, load private documents, or connect to a model or MCP server.

## Local browser walkthrough

Open the English walkthrough at `demo.en.html` and choose a module directly. Each module also links to the matching Traditional Chinese view:

- [Gateway](../demo.en.html?module=gateway) · [繁體中文](../demo.html?module=gateway): In **Allocation & Limits**, choose a Workspace and model, then select **Approve**. Approval alone does not change a native Team allowlist. Workspace is a local mapping. In **Models & Access**, choose an **Approved model** and select **Select** to simulate adding it to the native LiteLLM Team allowlist for that mapping. The **Demo scenario: simulate a timeout** checkbox makes the selection show **Needs readback**; use **Reconcile** to run the matching readback. A successful readback shows native Team **Selected**, while Runtime remains **Not verified**.
- [Financial OCR](../demo.en.html?module=ocr) · [繁體中文](../demo.html?module=ocr): Select **Create synthetic case** or open a case, then choose a provider, document type, and synthetic document. **Run recognition and masking** adds a document row with **Profile field values**, **Next Case request**, **Saved Raw response**, and **Parser fields / errors**. Recognition fills only the first two. Select **Run user financial summary evaluation** separately to populate the saved response and parser after schema and field-type checks.
- [Elasticsearch chat](../demo.en.html?module=chat) · [繁體中文](../demo.html?module=chat): The chat uses the fixed **Elasticsearch Ops** skill. Select a room or choose **New conversation**; the composer is disabled until a room is active. Choose a **Model**, type in **Enter a message. Enter to send; Shift+Enter for a new line.**, and use Enter to send. **Reset chat** clears the transcript while keeping the room; **Export chat** downloads only the synthetic local transcript. Expand **View MCP tool call** to inspect informational tool details.

The browser walkthrough is offline and synthetic. Its chat screen does not offer a primary skill dropdown or arbitrary allow/deny buttons. The separate Python sample demonstrates fail-closed tool listing and dispatch; that hardening is not a claim about the original chat UI or dispatch behavior.

## Run locally

```powershell
python -m pip install -r requirements-demo.txt
python examples/run_demo.py all
python -m unittest discover -s tests -p "test_examples.py" -v
```

Choose `gateway`, `ocr`, or `mcp` in place of `all` to run one example. The OCR example uses the `cryptography` package for AES-GCM. Its random mapping key exists only in the process memory; the example does not save or print it.

These standalone Python examples use in-memory fixtures and are separate from the persistent Flask runtime now included in `public_app/`. See the root [README](../README.md) for the SQLite-backed application and its optional configured service adapters. The examples remain useful as small isolated control-flow demonstrations; they do not invoke that application.

## What each example demonstrates

- **Gateway:** A repeat request with the same idempotency key, actor, and payload returns the saved result without another provider create call. A timeout after the fake native provider applies a write remains `UNKNOWN` until explicit readback confirms provider ID, operation ID, actor, payload, and fingerprint. A mismatch or unavailable readback stays `UNKNOWN`; reusing the key with a changed actor or payload is rejected. The provider is an in-memory fixture, not LiteLLM.
- **Financial OCR:** The fake extraction step represents model output before replacement. A configured profile allowlists model fields, drops unknown fields, adds document/page provenance, and replaces configured protected values with stable, document-scoped tokens. The reversible map is AES-GCM encrypted with a fresh nonce per value. Reversal requires an explicit authorization flag and adds an in-memory audit entry. This illustrates field handling; it does not detect every kind of PII, guarantee irreversible anonymization, or recalculate business formulas. The stage-one model sees the raw document. Only a selected on-premises inference provider keeps that model request local; an outbound model provider may receive the image or text.
- **Elasticsearch MCP Python sample:** The JSON-RPC `tools/call` shape and fixture response are handled entirely in memory. Tool visibility and dispatch both check the skill allowlist; missing configuration exposes no tools, and a denied direct dispatch never calls the fixture provider. The sample is deliberately stricter than the original application dispatch: the original tool-list helper has a fallback for missing skill configuration, and its call function is not itself a per-skill authorization boundary. This independent hardening example is not the browser chat UI and does not claim to reproduce the original dispatch implementation.

The flat sample OCR profile only forwards allowlisted JSON scalar fields plus a non-empty document ID and positive page number; nested values and group fields fail closed. Raw image bytes, extracted free text, and unknown fields are not put in the outbound payload. Synthetic names, account-like values, request IDs, and workspace names are fictional. No proprietary formulas, real records, endpoints, or secrets are included.

## Related diagrams

The authored Archify sources and generated HTML/SVG live in `../assets/diagrams/`. From the portfolio root, regenerate and validate them with:

```powershell
node tools/build_diagrams.mjs "C:\path\to\archify\archify"
```

Diagram regeneration uses the Archify viewer's standalone SVG exporter. Install the local browser helper once with `python -m pip install -r requirements-diagrams.txt` and `python -m playwright install chromium`.
