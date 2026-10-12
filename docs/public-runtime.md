# Local runtime

This checkout contains two distinct browser experiences:

- The live local app at [`app.en.html`](../app.en.html) or [`app.html`](../app.html) calls the Flask service in `public_app`. It stores workspaces, models, approvals, Gateway operations, OCR cases, and chat rooms in SQLite under `.local/runtime` by default.
- The source-derived [`offline walkthrough`](../demo.en.html?module=gateway) is a static reconstruction with deterministic browser fixtures. It does not call the runtime or Python examples and resets its state on reload.

## Start the app

Use Python 3.11 or later (verified with Python 3.14.5). From the repository root, create a virtual environment, install the runtime dependencies, and run the server.

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-runtime.txt
.venv\Scripts\python.exe -m public_app
```

**macOS / Linux**

```console
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python -m public_app
```

After installing `requirements-runtime.txt`, run the full runtime and example test suite:

**Windows PowerShell**

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

**macOS / Linux**

```console
.venv/bin/python -m unittest discover -s tests -v
```

Open <http://127.0.0.1:8000/>. The service binds to loopback by default. The local operator console has no authentication; keep it on the local machine and do not expose its port to a network. The application UI is served by this runtime; opening `app.html` as a `file://` page does not start the API.

## What runs locally

- **Gateway:** the Flask app manages a local Workspace/model registry and records Workspace approval separately from provider selection. When LiteLLM management is configured, selection writes to its native Team and verifies by reading the Team state back. Runtime use of a model remains a separate, unverified condition. The local timeout scenario is only for the local registry.
- **OCR:** RapidOCR processes an uploaded PNG/JPEG image on the local CPU. On the tested clean Windows install, the RapidOCR wheel included its default ONNX models and the first OCR request loaded them locally without a model download. Document records are encrypted in the local SQLite vault. Choosing a configured VLM sends the original, unmodified image to the operator-configured vision endpoint. The image is not de-identified before the VLM receives it; the UI requires an explicit confirmation before upload. Use only synthetic documents unless the endpoint and data handling are appropriate for the document.
- **Evaluation:** local validation checks field presence and types; it does not recompute financial formulas or eligibility. Configured LLM evaluation sends a minimized profile containing only allowlisted fields. Name and account values are replaced with document-scoped tokens; raw image, raw OCR text, source identifiers, and source-line provenance are excluded. The request retains field names and field-name provenance. This reduces what is sent but is pseudonymization, not irreversible anonymization. Use only synthetic documents unless the endpoint and data handling are appropriate for the case.
- **Search and chat:** search uses a local SQLite FTS5 index containing synthetic operational events unless Elasticsearch is configured. Chat search returns actual results from the selected search backend. Model-assisted chat calls the endpoint the operator configures and is unavailable until model settings are present.
- **MCP route:** `/mcp` accepts a constrained JSON-RPC subset for `tools/list` and `tools/call`, requires `context.active_skill="elasticsearch-ops"`, and exposes only the public search-oriented tool subset. It is not a general-purpose MCP server implementation or a drop-in standard MCP client endpoint.

## Endpoint configuration and data

The Connections page stores endpoint URLs and model names; it does not accept or return API keys. Put credentials in the ignored `.local/runtime-config.json` or server environment variables. Supported variable names include `PORTFOLIO_MODEL_API_KEY`, `PORTFOLIO_LITELLM_API_KEY`, and `PORTFOLIO_LITELLM_MASTER_KEY`. Never put credentials in a URL or commit the local configuration file.

The API can send requests to user-configured model, LiteLLM, VLM, or Elasticsearch endpoints. Those requests leave the local process. The app does not bundle those services, models, or credentials. This runtime supports model/LiteLLM credentials in local ignored configuration or server environment variables. Elasticsearch integration supports a directly reachable test endpoint without credentials; authenticated Elasticsearch is not configured. Browser view state resets on reload; runtime records persist in the local SQLite database. The separate Python examples use in-memory fake providers and do not write to this runtime database.

Use the offline walkthrough for a network-free visual tour. Use the local runtime when you want to exercise the actual Flask routes and local persistence.
