# Synthetic browser walkthrough

These scenarios describe controls in the English browser walkthrough at `demo.en.html`. Records and outcomes are synthetic; the walkthrough does not connect to the original services, models, documents, or MCP server. Use the in-page **繁體中文** switch to open the same module in Chinese; it preserves the selected module.

## AI Model Gateway

| Step | UI action | Walkthrough state |
| --- | --- | --- |
| Request setup | In **Allocation & Limits**, choose a Workspace and model | The access request is associated with the selected Workspace/model mapping. |
| Approval | Select **Approve** | Approval is recorded; it does not change a native Team allowlist. |
| Native Team selection | In Workspace **Models & Access**, choose an **Approved model** and select **Select** | The sample simulates adding the model to the native LiteLLM Team allowlist for that local Workspace mapping. |
| Uncertain outcome | Enable **Demo scenario: simulate a timeout** before selecting | The selection becomes **Needs readback** and exposes **Reconcile**. The fixture represents an unknown native outcome; it makes no live remote call. |
| Readback | Select **Reconcile** | A matching readback shows native Team **Selected**. Runtime remains **Not verified**. |

Workspace is a local mapping; the native object is the LiteLLM Team. Approval and adding a model to that Team allowlist are distinct actions. Neither approval nor matching readback asserts that a model is available at runtime.

## Financial OCR

| Step | UI action | Walkthrough state |
| --- | --- | --- |
| Open a case | Select **Create synthetic case** or **Open** an existing case | The case detail view shows the selected synthetic case. |
| Configure a document | Select a provider, document type, and synthetic document | The chosen fixture is ready for stage one. |
| Recognize and mask | Select **Run recognition and masking** | A document row appears with **Profile field values**, **Next Case request**, **Saved Raw response**, and **Parser fields / errors**. Recognition fills only the first two. |
| Evaluate the case | Select **Run user financial summary evaluation** separately | The saved response and parser are populated after schema and field-type checks. The parser checks JSON structure and field types only. |

Recognition and masking do not run the financial summary action. The browser walkthrough uses fictional fixtures and does not represent a live OCR or financial decision.

## Elasticsearch chat

| Step | UI action | Walkthrough state |
| --- | --- | --- |
| Open a conversation | Select an existing room or choose **New conversation** | The fixed **Elasticsearch Ops** skill is used; there is no skill dropdown. |
| Choose a model and compose | Select **Model** and use **Enter a message. Enter to send; Shift+Enter for a new line.** | The composer is disabled until a room is selected or created. Enter sends; Shift+Enter inserts a newline. |
| Review the response | Send a message and expand **View MCP tool call** | A deterministic synthetic answer appears with informational tool-call details. |
| Reset or export | Use **Reset chat** or **Export chat** | Reset clears the transcript but keeps the selected room. Export downloads only the synthetic local transcript. |

The browser walkthrough does not expose arbitrary allowed-tool or denied-tool buttons. The separate Python MCP example demonstrates fail-closed tool-list and dispatch checks; that additional hardening is not a claim about the original chat UI or dispatch behavior.
