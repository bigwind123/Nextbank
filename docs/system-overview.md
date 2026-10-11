# System overview

The system has a platform management product and two applications. The Gateway control plane manages model-platform resources; application prompts and tools follow separate service paths.

## Components and responsibilities

| Component | Responsibility | Data authority / boundary |
| --- | --- | --- |
| Gateway management UI/API (Flask module) | Admin browser UI, management workflows, input validation, and operation status | Uses management authorization on the server to read/write LiteLLM native resources; does not relay model prompts |
| LiteLLM platform | Native model definitions, Team model allowlists, and inference gateway | Owns its native platform objects and serves inference through its separately configured endpoint |
| Financial OCR | Page image extraction, pseudonym vault workflow, profile-based case payload and output checks | Stage 1 uses a configured VLM provider; Stage 2 uses its separately configured analysis endpoint |
| Operations chat | Skill-aware model-visible tool list and conversation workflow | Calls its separately configured model endpoint, then invokes tools using JSON-RPC MCP |
| MCP / Elasticsearch | Execute permitted search and operations queries | The sample is read-only; the original application has additional integrations and mutation-capable tools |

## Request paths

```text
Platform administrator
    -> Flask UI/API
    -> LiteLLM management API
    -> native Team, model, access and usage resources; local Workspace mapping

OCR application
    -> selected Stage 1 VLM endpoint (page image)
    -> local processing and document-scoped encrypted pseudonym mapping
    -> profile-allowlisted, provenance-bearing Stage 2 payload
    -> separately configured analysis endpoint
    -> schema/profile checks and human review

Operations user
    -> chat application
    -> independently configured inference endpoint
    -> skill-selected model-visible tools
    -> JSON-RPC MCP service
    -> Elasticsearch query result
```

The OCR locality boundary depends on the Stage 1 provider selected at runtime. If that provider is on-prem and actually reachable within the local boundary, the input image can remain there; configuration capability alone does not prove that every run is local. Stage 1 sees the image before tokenization. Stage 2 receives only published-profile allowlisted values and source page metadata. Its structured response is checked against expected types and profile rules; this does not mean the complete business evaluation is recomputed locally.

The operations chat has some Elasticsearch query guidance and skill-scoped tool selection. In the original application, a missing skill configuration could fall back to all tools and dispatch did not receive the active skill context. The public sample rebuild closes this gap with fail-closed selection and a dispatch authorization check. That improvement must not be attributed to the original application.

See the [platform overview diagram](../assets/diagrams/platform-overview.html), [OCR diagram](../assets/diagrams/financial-ocr.html), and [MCP diagram](../assets/diagrams/elasticsearch-mcp.html). These are conceptual explanations and do not expose deployment endpoints or topology.
