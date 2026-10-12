from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from .config import URL_SETTINGS, _validate_endpoint
from .providers import LocalRegistryProvider, OperationProvenance, ProviderError, WriteUncertain


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _error(code: str, message: str, status: int):
    return jsonify({"error": {"code": code, "message": message}}), status


def _body() -> dict[str, Any]:
    value = request.get_json(silent=True)
    if not isinstance(value, dict):
        raise ValueError("body_must_be_object")
    return value


def _text(value: Any, field: str, *, required: bool = True, limit: int = 160) -> str:
    if value is None and not required:
        return ""
    if not isinstance(value, str):
        raise ValueError(f"{field}_must_be_string")
    result = value.strip()
    if required and not result:
        raise ValueError(f"{field}_required")
    if len(result) > limit:
        raise ValueError(f"{field}_too_long")
    return result


def _database():
    return current_app.extensions["portfolio_database"]


def _provider():
    return current_app.extensions["portfolio_gateway_provider"]


def _provider_mode() -> str:
    return current_app.extensions["portfolio_gateway_provider_mode"]


def _local_workspace(row) -> dict[str, Any]:
    workspace = dict(row)
    workspace["provider_mode"] = _provider_mode()
    workspace["approved_model_ids"] = []
    workspace["selected_model_ids"] = []
    return workspace


def _workspace_snapshot(workspace_id: str) -> dict[str, Any] | None:
    with _database().connect() as connection:
        row = _get_workspace(connection, workspace_id)
        if not row:
            return None
        workspace = _local_workspace(row)
        workspace["approved_model_ids"] = [r[0] for r in connection.execute(
            "SELECT model_id FROM approvals WHERE workspace_id=? ORDER BY model_id", (workspace_id,)
        )]
        workspace["selected_model_ids"] = [r[0] for r in connection.execute(
            "SELECT model_id FROM workspace_selections WHERE workspace_id=? ORDER BY model_id", (workspace_id,)
        )]
        return workspace


def _get_workspace(connection, workspace_id: str):
    return connection.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()


def _get_model(connection, model_id: str):
    return connection.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()


def _get_operation(connection, operation_id: str):
    return connection.execute("SELECT * FROM gateway_operations WHERE id = ?", (operation_id,)).fetchone()


def _operation_dict(row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "idempotency_key": row["idempotency_key"],
        "workspace_id": row["workspace_id"],
        "model_id": row["model_id"],
        "state": row["state"],
        "provider_mode": row["provider_mode"],
        "provider_id": row["provider_id"] or None,
        "error_code": row["error_code"] or None,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _make_provenance(row) -> OperationProvenance:
    payload = json.loads(row["payload_json"])
    return OperationProvenance(
        operation_id=row["id"], actor_id=row["actor_id"], fingerprint=row["fingerprint"],
        workspace_id=row["workspace_id"], model_id=row["model_id"], model_name=payload["model_name"],
    )


def _store_result(operation_id: str, state: str, provider_id: str = "", error_code: str = "") -> None:
    with _database().connect() as connection:
        connection.execute(
            "UPDATE gateway_operations SET state = ?, provider_id = ?, error_code = ?, updated_at = ? WHERE id = ?",
            (state, provider_id, error_code, utc_now(), operation_id),
        )
        if state == "selected":
            row = _get_operation(connection, operation_id)
            connection.execute(
                """INSERT INTO workspace_selections(workspace_id, model_id, operation_id, selected_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(workspace_id, model_id) DO UPDATE SET
                     operation_id = excluded.operation_id, selected_at = excluded.selected_at""",
                (row["workspace_id"], row["model_id"], operation_id, utc_now()),
            )


def _readback_matches(row, receipt) -> bool:
    if not receipt:
        return False
    expected = _make_provenance(row)
    if row["provider_mode"] == "litellm_management":
        expected_team_id = json.loads(row["payload_json"]).get("native_team_id")
        if not expected_team_id or receipt.get("provider_id") != expected_team_id:
            return False
    return all(receipt.get(key) == value for key, value in {
        "operation_id": expected.operation_id,
        "workspace_id": expected.workspace_id,
        "model_id": expected.model_id,
        "actor_id": expected.actor_id,
        "fingerprint": expected.fingerprint,
    }.items()) and bool(receipt.get("provider_id"))


def _reconcile_row(row):
    if row["state"] == "selected":
        return row, False
    db = _database()
    with db.connect() as connection:
        workspace = _get_workspace(connection, row["workspace_id"])
    if not workspace:
        _store_result(row["id"], "unknown", error_code="workspace_missing")
        with db.connect() as connection:
            return _get_operation(connection, row["id"]), False
    provider = _provider()
    if provider is None:
        _store_result(row["id"], "unknown", error_code="provider_unconfigured")
        with db.connect() as connection:
            return _get_operation(connection, row["id"]), False
    try:
        receipt = provider.readback(_make_provenance(row), workspace["native_team_id"])
    except Exception:
        receipt = None
    if _readback_matches(row, receipt):
        _store_result(row["id"], "selected", str(receipt["provider_id"]))
        with db.connect() as connection:
            return _get_operation(connection, row["id"]), True
    _store_result(row["id"], "unknown", error_code="readback_unconfirmed")
    with db.connect() as connection:
        return _get_operation(connection, row["id"]), False


def register_gateway(app, config, db) -> None:
    bp = Blueprint("gateway_api", __name__, url_prefix="/api")
    app.extensions["portfolio_database"] = db
    if "portfolio_gateway_provider" not in app.extensions:
        app.extensions["portfolio_gateway_provider"] = LocalRegistryProvider(db)

    @bp.get("/health")
    def health():
        runtime = current_app.config["PORTFOLIO_CONFIG"]
        modules = current_app.extensions.get("portfolio_modules", {})
        # Settings can change at runtime, so capability modes must be derived
        # from the current config instead of the registration-time snapshot.
        chat_mode = "not_installed"
        if modules.get("chat"):
            chat_mode = "configured-model" if runtime.get("model_base_url") and runtime.get("model_name") else "search-only"
        mcp_mode = "not_installed"
        if modules.get("mcp"):
            mcp_mode = "elasticsearch" if runtime.get("es_url") else "sqlite-fts5"
        ocr_mode = current_app.extensions.get("portfolio_ocr_mode", "not_installed") if modules.get("ocr") else "not_installed"
        return jsonify({
            "status": "ok",
            "registry_mode": _provider_mode(),
            "gateway_provider_mode": _provider_mode(),
            "inference_configured": bool(runtime.get("model_base_url") and runtime.get("model_name")),
            "ocr_mode": ocr_mode,
            "chat_mode": chat_mode,
            "mcp_mode": mcp_mode,
        })

    @bp.get("/settings")
    def get_settings():
        runtime = current_app.config["PORTFOLIO_CONFIG"]
        result = {key: runtime.get(key, "") for key in (
            "model_base_url", "model_name", "vision_model_name", "es_url", "litellm_url",
        )}
        result["gateway_provider_mode"] = _provider_mode()
        return jsonify({"settings": result})

    @bp.post("/settings")
    def update_settings():
        try:
            body = _body()
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        allowed = {"model_base_url", "model_name", "vision_model_name", "es_url", "litellm_url"}
        if set(body) - allowed:
            return _error("invalid_request", "Only public endpoint and model settings can be changed here.", 400)
        values = {}
        for key, value in body.items():
            try:
                values[key] = _text(value, key, required=False, limit=2048)
                if key in URL_SETTINGS and values[key]:
                    _validate_endpoint(key, values[key])
            except RuntimeError:
                return _error("invalid_endpoint", f"{key} must be an http(s) URL without embedded credentials, query, or fragment.", 400)
            except ValueError as exc:
                return _error("invalid_request", str(exc), 400)
        runtime = current_app.config["PORTFOLIO_CONFIG"]
        if ("litellm_url" in values and values["litellm_url"] != runtime.get("litellm_url", "")
                and (runtime.get("litellm_management_api_key") or runtime.get("litellm_management_master_key"))):
            return _error("setting_locked", "Change the LiteLLM management URL in the ignored local config file while credentials are configured.", 409)
        with db.connect() as connection:
            for key, value in values.items():
                connection.execute("""INSERT INTO runtime_settings(name, value) VALUES(?, ?)
                    ON CONFLICT(name) DO UPDATE SET value=excluded.value""", (key, value))
        runtime.update(values)
        app.extensions["portfolio_gateway_provider"], app.extensions["portfolio_gateway_provider_mode"] = _provider_for_config(runtime, db)
        return jsonify({"settings": {**{key: runtime.get(key, "") for key in allowed}, "gateway_provider_mode": _provider_mode()}})

    @bp.get("/workspaces")
    def list_workspaces():
        with db.connect() as connection:
            workspaces = connection.execute("SELECT * FROM workspaces ORDER BY name COLLATE NOCASE, id").fetchall()
            result = []
            for row in workspaces:
                item = _local_workspace(row)
                item["approved_model_ids"] = [r[0] for r in connection.execute(
                    "SELECT model_id FROM approvals WHERE workspace_id = ? ORDER BY model_id", (row["id"],)
                )]
                item["selected_model_ids"] = [r[0] for r in connection.execute(
                    "SELECT model_id FROM workspace_selections WHERE workspace_id = ? ORDER BY model_id", (row["id"],)
                )]
                result.append(item)
        return jsonify({"workspaces": result})

    @bp.get("/workspaces/<workspace_id>")
    def get_workspace(workspace_id: str):
        workspace = _workspace_snapshot(workspace_id)
        if not workspace:
            return _error("not_found", "Workspace not found.", 404)
        return jsonify({"workspace": workspace})

    @bp.post("/workspaces")
    def create_workspace():
        try:
            body = _body()
            if set(body) - {"name", "native_team_id"}:
                raise ValueError("Only name and native_team_id can be supplied.")
            name = _text(body.get("name"), "name", limit=120)
            native_team_id = _text(body.get("native_team_id", ""), "native_team_id", required=False, limit=200)
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        workspace_id = uuid.uuid4().hex
        created_at = utc_now()
        try:
            with db.connect() as connection:
                connection.execute("INSERT INTO workspaces(id, name, native_team_id, created_at) VALUES(?,?,?,?)",
                                   (workspace_id, name, native_team_id, created_at))
        except sqlite3.IntegrityError:
            return _error("conflict", "A Workspace with that name already exists.", 409)
        return jsonify({"workspace": {"id": workspace_id, "name": name, "native_team_id": native_team_id,
                                       "created_at": created_at, "provider_mode": _provider_mode(),
                                       "approved_model_ids": [], "selected_model_ids": []}}), 201

    @bp.patch("/workspaces/<workspace_id>")
    def update_workspace(workspace_id: str):
        try:
            body = _body()
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        if not body or set(body) - {"name", "native_team_id"}:
            return _error("invalid_request", "Supply name and/or native_team_id only.", 400)
        values = {}
        try:
            for key, value in body.items():
                values[key] = _text(value, key, required=(key == "name"), limit=120 if key == "name" else 200)
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        with db.connect() as connection:
            current = _get_workspace(connection, workspace_id)
            if not current:
                return _error("not_found", "Workspace not found.", 404)
            if "native_team_id" in values and values["native_team_id"] != current["native_team_id"]:
                references = connection.execute("""SELECT 1 FROM gateway_operations WHERE workspace_id=? LIMIT 1""", (workspace_id,)).fetchone()
                if references:
                    return _error("mapping_locked", "The native Team mapping is locked after the first Gateway operation.", 409)
            assignments = ", ".join(f"{key} = ?" for key in values)
            try:
                connection.execute(f"UPDATE workspaces SET {assignments} WHERE id = ?", (*values.values(), workspace_id))
            except sqlite3.IntegrityError:
                return _error("conflict", "A Workspace with that name already exists.", 409)
            updated = _get_workspace(connection, workspace_id)
        return jsonify({"workspace": _workspace_snapshot(workspace_id)})

    @bp.delete("/workspaces/<workspace_id>")
    def delete_workspace(workspace_id: str):
        with db.connect() as connection:
            if not _get_workspace(connection, workspace_id):
                return _error("not_found", "Workspace not found.", 404)
            referenced = connection.execute("SELECT 1 FROM gateway_operations WHERE workspace_id=? LIMIT 1", (workspace_id,)).fetchone()
            if referenced:
                return _error("workspace_in_use", "A Workspace with Gateway operations cannot be deleted.", 409)
            connection.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
        return "", 204

    @bp.get("/models")
    def list_models():
        with db.connect() as connection:
            rows = connection.execute("SELECT id, name, created_at FROM models ORDER BY name COLLATE NOCASE, id").fetchall()
        return jsonify({"models": [dict(row) for row in rows]})

    @bp.get("/models/<model_id>")
    def get_model(model_id: str):
        with db.connect() as connection:
            model = _get_model(connection, model_id)
        if not model:
            return _error("not_found", "Model not found.", 404)
        return jsonify({"model": dict(model)})

    @bp.post("/models")
    def create_model():
        try:
            body = _body()
            if set(body) != {"name"}:
                raise ValueError("Only the model name can be supplied.")
            name = _text(body.get("name"), "name", limit=200)
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        model_id = uuid.uuid4().hex
        created_at = utc_now()
        try:
            with db.connect() as connection:
                connection.execute("INSERT INTO models(id, name, created_at) VALUES(?,?,?)", (model_id, name, created_at))
        except sqlite3.IntegrityError:
            return _error("conflict", "A model with that name already exists.", 409)
        return jsonify({"model": {"id": model_id, "name": name, "created_at": created_at}}), 201

    @bp.patch("/models/<model_id>")
    def update_model(model_id: str):
        try:
            body = _body()
            if set(body) != {"name"}:
                raise ValueError("Only the model name can be changed.")
            name = _text(body.get("name"), "name", limit=200)
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        with db.connect() as connection:
            current = _get_model(connection, model_id)
            if not current:
                return _error("not_found", "Model not found.", 404)
            referenced = connection.execute("""SELECT 1 FROM gateway_operations WHERE model_id=? LIMIT 1""", (model_id,)).fetchone()
            if referenced:
                return _error("model_in_use", "A model with Gateway operations cannot be renamed.", 409)
            try:
                connection.execute("UPDATE models SET name=? WHERE id=?", (name, model_id))
            except sqlite3.IntegrityError:
                return _error("conflict", "A model with that name already exists.", 409)
            updated = _get_model(connection, model_id)
        return jsonify({"model": dict(updated)})

    @bp.delete("/models/<model_id>")
    def delete_model(model_id: str):
        with db.connect() as connection:
            if not _get_model(connection, model_id):
                return _error("not_found", "Model not found.", 404)
            referenced = connection.execute("SELECT 1 FROM gateway_operations WHERE model_id=? LIMIT 1", (model_id,)).fetchone()
            if referenced:
                return _error("model_in_use", "A model with Gateway operations cannot be deleted.", 409)
            connection.execute("DELETE FROM models WHERE id = ?", (model_id,))
        return "", 204

    @bp.post("/workspaces/<workspace_id>/approve")
    def approve_model(workspace_id: str):
        try:
            body = _body()
            if set(body) != {"model_id"}:
                raise ValueError("Only model_id can be supplied for approval.")
            model_id = _text(body.get("model_id"), "model_id", limit=80)
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        with db.connect() as connection:
            workspace, model = _get_workspace(connection, workspace_id), _get_model(connection, model_id)
            if not workspace:
                return _error("not_found", "Workspace not found.", 404)
            if not model:
                return _error("not_found", "Model not found.", 404)
            now = utc_now()
            connection.execute("""INSERT INTO approvals(workspace_id, model_id, state, created_at)
                VALUES(?, ?, 'approved', ?) ON CONFLICT(workspace_id, model_id)
                DO UPDATE SET state='approved', created_at=excluded.created_at""", (workspace_id, model_id, now))
        return jsonify({"approval": {"workspace_id": workspace_id, "model_id": model_id, "state": "approved", "created_at": now}})

    @bp.post("/workspaces/<workspace_id>/select")
    def select_model(workspace_id: str):
        try:
            body = _body()
            if set(body) - {"model_id", "idempotency_key", "actor_id", "simulate_timeout"}:
                raise ValueError("The selection request contains unsupported fields.")
            model_id = _text(body.get("model_id"), "model_id", limit=80)
            key = _text(body.get("idempotency_key") or request.headers.get("Idempotency-Key"), "idempotency_key", limit=200)
            actor = _text(body.get("actor_id", request.headers.get("X-Actor-ID", "local-user")), "actor_id", limit=120)
            simulate = body.get("simulate_timeout", False)
            if not isinstance(simulate, bool):
                raise ValueError("simulate_timeout_must_be_boolean")
        except ValueError as exc:
            return _error("invalid_request", str(exc), 400)
        with db.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            workspace, model = _get_workspace(connection, workspace_id), _get_model(connection, model_id)
            if not workspace:
                return _error("not_found", "Workspace not found.", 404)
            if not model:
                return _error("not_found", "Model not found.", 404)
            approval = connection.execute("SELECT 1 FROM approvals WHERE workspace_id=? AND model_id=?", (workspace_id, model_id)).fetchone()
            if not approval:
                return _error("approval_required", "Approve this model for the Workspace before selecting it.", 409)
            provider = _provider()
            if provider is None:
                return _error("provider_unconfigured", "LiteLLM management is configured without a management credential.", 503)
            payload = {"workspace_id": workspace_id, "model_id": model_id, "model_name": model["name"],
                       "native_team_id": workspace["native_team_id"]}
            fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            existing = connection.execute("SELECT * FROM gateway_operations WHERE idempotency_key=?", (key,)).fetchone()
            if existing:
                if existing["actor_id"] != actor or existing["fingerprint"] != fingerprint:
                    return _error("idempotency_conflict", "This idempotency key is already bound to a different actor or request.", 409)
                operation_id = existing["id"]
                existing_state = existing["state"]
            else:
                unresolved = connection.execute(
                    """SELECT * FROM gateway_operations
                       WHERE workspace_id=? AND model_id=? AND state IN ('unknown','pending')
                       ORDER BY created_at LIMIT 1""",
                    (workspace_id, model_id),
                ).fetchone()
                if unresolved:
                    return jsonify({
                        "error": {"code": "operation_unresolved", "message": "Reconcile the existing uncertain operation before starting another selection."},
                        "operation": _operation_dict(unresolved),
                    }), 409
                operation_id = uuid.uuid4().hex
                now = utc_now()
                connection.execute("""INSERT INTO gateway_operations
                    (id, idempotency_key, workspace_id, model_id, actor_id, fingerprint, payload_json,
                     state, provider_mode, created_at, updated_at)
                    VALUES(?,?,?,?,?,?,?,'pending',?,?,?)""",
                    (operation_id, key, workspace_id, model_id, actor, fingerprint,
                     json.dumps(payload, sort_keys=True), _provider_mode(), now, now))
                existing_state = "new"
        if existing_state in {"unknown", "pending"}:
            with db.connect() as connection:
                op = _get_operation(connection, operation_id)
            op, confirmed = _reconcile_row(op)
            status = 200 if confirmed or op["state"] == "selected" else 202
            return jsonify({"operation": _operation_dict(op), "workspace": _workspace_snapshot(workspace_id)}), status
        if existing_state == "selected":
            with db.connect() as connection:
                op = _get_operation(connection, operation_id)
            return jsonify({"operation": _operation_dict(op), "workspace": _workspace_snapshot(workspace_id)}), 200
        with db.connect() as connection:
            op = _get_operation(connection, operation_id)
        try:
            provider_id = provider.apply_selection(_make_provenance(op), workspace["native_team_id"], simulate_timeout=simulate)
        except WriteUncertain as exc:
            _store_result(operation_id, "unknown", error_code=str(exc))
            with db.connect() as connection:
                op = _get_operation(connection, operation_id)
            return jsonify({"operation": _operation_dict(op), "workspace": _workspace_snapshot(workspace_id)}), 202
        except ProviderError as exc:
            _store_result(operation_id, "unknown", error_code=str(exc))
            with db.connect() as connection:
                op = _get_operation(connection, operation_id)
            return jsonify({"operation": _operation_dict(op), "workspace": _workspace_snapshot(workspace_id)}), 202
        try:
            receipt = provider.readback(_make_provenance(op), workspace["native_team_id"])
        except Exception:
            receipt = None
        if not _readback_matches(op, receipt):
            _store_result(operation_id, "unknown", error_code="readback_unconfirmed")
            with db.connect() as connection:
                op = _get_operation(connection, operation_id)
            return jsonify({"operation": _operation_dict(op), "workspace": _workspace_snapshot(workspace_id)}), 202
        _store_result(operation_id, "selected", provider_id)
        with db.connect() as connection:
            op = _get_operation(connection, operation_id)
        return jsonify({"operation": _operation_dict(op), "workspace": _workspace_snapshot(workspace_id)}), 200

    @bp.post("/operations/<operation_id>/reconcile")
    def reconcile_operation(operation_id: str):
        with db.connect() as connection:
            row = _get_operation(connection, operation_id)
        if not row:
            return _error("not_found", "Operation not found.", 404)
        updated, confirmed = _reconcile_row(row)
        return jsonify({"operation": _operation_dict(updated), "confirmed": confirmed}), 200 if confirmed or updated["state"] == "selected" else 202

    @bp.get("/operations")
    def list_operations():
        with db.connect() as connection:
            rows = connection.execute("SELECT * FROM gateway_operations ORDER BY created_at DESC LIMIT 200").fetchall()
        return jsonify({"operations": [_operation_dict(row) for row in rows]})

    app.register_blueprint(bp)


def _provider_for_config(config, db):
    from .providers import LiteLLMProvider
    credential = config.get("litellm_management_api_key") or config.get("litellm_management_master_key")
    if config.get("litellm_url") and credential:
        return LiteLLMProvider(config["litellm_url"], credential), "litellm_management"
    if config.get("litellm_url"):
        return None, "litellm_management_unconfigured"
    return LocalRegistryProvider(db), "local_registry"
