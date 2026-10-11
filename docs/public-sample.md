# Public sample

The standalone Python examples use synthetic records and local logic. They make no network calls and contain no real endpoints, credentials, documents, logs, or identifiers.

## Run

From the portfolio root, Gateway and MCP run without extra Python packages:

```console
python examples/run_demo.py gateway
python examples/run_demo.py mcp
```

The OCR payload example, the combined `all` command, and the sample checks require `cryptography` for AES-GCM token mapping. Install it before running them:

```console
python -m pip install -r requirements-demo.txt
python examples/run_demo.py ocr
python examples/run_demo.py all
python -m unittest discover -s tests -v
```

The sample is designed to reject unknown skills and re-check tool authorization at dispatch. This is a deliberate hardening in the rebuilt public example. The source chat application has older paths where missing skill configuration defaults to all tools and dispatch does not receive the active skill context.

The source-derived browser walkthrough is a separate static reconstruction: [Gateway](../demo.en.html?module=gateway), [OCR](../demo.en.html?module=ocr), and [chat](../demo.en.html?module=chat). Its controls use deterministic synthetic fixtures; they do not execute these Python examples, contact a backend, invoke a model, read a document, or query Elasticsearch.
