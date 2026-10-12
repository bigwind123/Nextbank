from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


class ProviderError(RuntimeError):
    """Safe, user-facing provider error with no response body or credential data."""


class WriteUncertain(ProviderError):
    pass


@dataclass(frozen=True)
class OperationProvenance:
    operation_id: str
    actor_id: str
    fingerprint: str
    workspace_id: str
    model_id: str
    model_name: str


class LocalRegistryProvider:
    mode = "local_registry"

    def __init__(self, db):
        self.db = db

    def apply_selection(self, operation: OperationProvenance, native_team_id: str = "", simulate_timeout: bool = False) -> str:
        provider_id = f"registry-{operation.operation_id}"
        with self.db.connect() as connection:
            connection.execute(
                """INSERT OR IGNORE INTO registry_selection_receipts
                   (operation_id, workspace_id, model_id, actor_id, fingerprint, provider_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (operation.operation_id, operation.workspace_id, operation.model_id, operation.actor_id,
                 operation.fingerprint, provider_id),
            )
        if simulate_timeout:
            raise WriteUncertain("simulated_timeout_after_apply")
        return provider_id

    def readback(self, operation: OperationProvenance, native_team_id: str = "") -> dict[str, Any] | None:
        with self.db.connect() as connection:
            row = connection.execute(
                "SELECT * FROM registry_selection_receipts WHERE operation_id = ?", (operation.operation_id,)
            ).fetchone()
            return dict(row) if row else None


class LiteLLMProvider:
    """Small optional management adapter for LiteLLM /team/update and /team/info.

    Inference clients do not use this adapter. Team IDs must be explicitly mapped on
    a local Workspace, and bearer credentials are never included in exceptions.
    """

    mode = "litellm_management"

    def __init__(self, base_url: str, api_key: str, timeout: float = 5.0):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("LiteLLM management URL must be an http(s) URL without embedded credentials, query, or fragment")
        self.base_url = base_url.rstrip("/") + "/"
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method: str, path: str, *, data: dict[str, Any] | None = None, query: dict[str, str] | None = None) -> dict[str, Any]:
        url = urljoin(self.base_url, path.lstrip("/"))
        if query:
            url += "?" + urlencode(query)
        body = json.dumps(data).encode("utf-8") if data is not None else None
        request = Request(url, data=body, method=method, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        try:
            # Management credentials must never follow a redirect to a second
            # authority. Treat redirects as uncertain provider failures.
            class _NoRedirect(HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None

            with build_opener(_NoRedirect()).open(request, timeout=self.timeout) as response:
                decoded = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            exc.close()
            raise WriteUncertain("litellm_management_unavailable") from exc
        except (TimeoutError, OSError, URLError, json.JSONDecodeError) as exc:
            raise WriteUncertain("litellm_management_unavailable") from exc
        if not isinstance(decoded, dict):
            raise ProviderError("litellm_invalid_response")
        return decoded

    @staticmethod
    def _team_info(response: dict[str, Any]) -> dict[str, Any]:
        # LiteLLM /team/info wraps the team row in `team_info`; fields at the
        # response top level are not the team record.
        team_info = response.get("team_info")
        if not isinstance(team_info, dict):
            raise ProviderError("litellm_team_info_missing")
        return team_info

    def apply_selection(self, operation: OperationProvenance, native_team_id: str = "", simulate_timeout: bool = False) -> str:
        if not native_team_id:
            raise ProviderError("native_team_mapping_required")
        # Read first so an update preserves existing Team models and metadata.
        current = self._team_info(self._request("GET", "/team/info", query={"team_id": native_team_id}))
        models = current.get("models")
        metadata = current.get("metadata")
        if metadata is None:
            metadata = {}
        if current.get("team_id") != native_team_id or not isinstance(models, list) or not all(isinstance(item, str) for item in models) or not isinstance(metadata, dict):
            raise ProviderError("litellm_team_shape_invalid")
        next_models = sorted(set(str(value) for value in models) | {operation.model_name})
        next_metadata = dict(metadata)
        raw_op_map = next_metadata.get("portfolio_operations") or {}
        if not isinstance(raw_op_map, dict):
            raise ProviderError("litellm_provenance_shape_invalid")
        op_map = dict(raw_op_map)
        op_map[operation.operation_id] = {
            "actor_id": operation.actor_id,
            "fingerprint": operation.fingerprint,
            "workspace_id": operation.workspace_id,
            "model_id": operation.model_id,
        }
        next_metadata["portfolio_operations"] = op_map
        self._request("POST", "/team/update", data={
            "team_id": native_team_id,
            "models": next_models,
            "metadata": next_metadata,
        })
        if simulate_timeout:
            raise WriteUncertain("simulated_timeout_after_apply")
        return native_team_id

    def readback(self, operation: OperationProvenance, native_team_id: str = "") -> dict[str, Any] | None:
        if not native_team_id:
            return None
        try:
            current = self._team_info(self._request("GET", "/team/info", query={"team_id": native_team_id}))
        except ProviderError:
            return None
        models = current.get("models")
        metadata = current.get("metadata")
        if metadata is None:
            metadata = {}
        if current.get("team_id") != native_team_id or not isinstance(models, list) or not all(isinstance(item, str) for item in models) or not isinstance(metadata, dict):
            return None
        operation_map = metadata.get("portfolio_operations") or {}
        if not isinstance(operation_map, dict):
            return None
        provenance = operation_map.get(operation.operation_id)
        if not isinstance(provenance, dict) or operation.model_name not in models:
            return None
        return {
            "operation_id": operation.operation_id,
            "workspace_id": provenance.get("workspace_id"),
            "model_id": provenance.get("model_id"),
            "actor_id": provenance.get("actor_id"),
            "fingerprint": provenance.get("fingerprint"),
            "provider_id": native_team_id,
        }
