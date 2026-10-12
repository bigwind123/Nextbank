from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import requests
from flask import Flask, jsonify, request


ACTIVE_SKILL = "elasticsearch-ops"
SKILL_TOOLS = {
    "es_search": "Search operational events in the public runtime event index.",
    "es_list_indices": "List public runtime event indices.",
    "es_get_mappings": "Read the mapping for the public runtime event index.",
    "es_get_shards": "Read shard status for the public runtime event index.",
}
PUBLIC_INDEX = "public-ops-events"


def register_mcp(app: Flask, config: dict[str, Any], db) -> None:
    _initialize_events(db)
    app.extensions["portfolio_mcp_mode"] = "sqlite-fts5" if not config.get("es_url") else "elasticsearch"

    @app.get("/api/events/search")
    def events_search():
        q = (request.args.get("q") or "").strip()
        try:
            limit = max(1, min(int(request.args.get("limit", "20")), 100))
        except ValueError:
            return jsonify({"error": {"code": "invalid_limit", "message": "limit must be an integer"}}), 400
        try:
            result = search_events(q, limit, config, db)
        except RuntimeError as exc:
            return _provider_error(exc)
        return jsonify(result)

    @app.post("/api/events")
    def events_create():
        body = request.get_json(silent=True) or {}
        service = _clean_text(body.get("service"), 80)
        level = _clean_text(body.get("level", "info"), 20).lower()
        message = _clean_text(body.get("message"), 2000)
        if not service or not message or level not in {"debug", "info", "warning", "error", "critical"}:
            return jsonify({"error": {"code": "invalid_event", "message": "service, message, and a supported level are required"}}), 400
        timestamp = _clean_text(body.get("timestamp"), 80) or datetime.now(timezone.utc).isoformat(timespec="seconds")
        event_id = str(uuid.uuid4())
        if config.get("es_url"):
            try:
                _es_request(config, "POST", f"/{PUBLIC_INDEX}/_doc/{event_id}?refresh=wait_for", {"service": service, "level": level, "message": message, "timestamp": timestamp})
            except RuntimeError as exc:
                return _provider_error(exc)
        else:
            with db.connect() as connection:
                connection.execute("INSERT INTO runtime_events(id, service, level, message, timestamp) VALUES(?,?,?,?,?)", (event_id, service, level, message, timestamp))
                connection.execute("INSERT INTO runtime_events_fts(event_id, service, level, message) VALUES(?,?,?,?)", (event_id, service, level, message))
        return jsonify({"event": {"id": event_id, "service": service, "level": level, "message": message, "timestamp": timestamp}, "backend": _backend(config)}), 201

    @app.post("/mcp")
    def mcp_endpoint():
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0" or not isinstance(payload.get("method"), str):
            return _jsonrpc_error(None, -32600, "Invalid JSON-RPC request", 400)
        method = payload["method"]
        params = payload.get("params", {})
        if not isinstance(params, dict):
            return _jsonrpc_error(payload.get("id"), -32602, "params must be an object", 400)
        context = payload.get("context")
        skill = context.get("active_skill") if isinstance(context, dict) else None
        if not skill:
            return _jsonrpc_error(payload.get("id"), -32001, "Required skill context is missing", 403)
        if skill != ACTIVE_SKILL:
            return _jsonrpc_error(payload.get("id"), -32002, "Skill is not allowed for this runtime", 403)
        if method == "tools/list":
            tools = [{"name": name, "description": description, "inputSchema": _tool_schema(name)} for name, description in SKILL_TOOLS.items()]
            return jsonify({"jsonrpc": "2.0", "id": payload.get("id"), "result": {"tools": tools}})
        if method == "tools/call":
            name = params.get("name")
            if not isinstance(name, str) or name not in SKILL_TOOLS:
                return _jsonrpc_error(payload.get("id"), -32003, "Tool is not allowed for this skill", 403)
            arguments = params.get("arguments", {})
            if not isinstance(arguments, dict):
                return _jsonrpc_error(payload.get("id"), -32602, "arguments must be an object", 400)
            try:
                result = dispatch_tool_call(skill, name, arguments, config, db)
            except ValueError as exc:
                return _jsonrpc_error(payload.get("id"), -32602, str(exc), 400)
            except RuntimeError as exc:
                return _jsonrpc_error(payload.get("id"), -32010, _safe_error(str(exc)), 502)
            return jsonify({"jsonrpc": "2.0", "id": payload.get("id"), "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "structuredContent": result}})
        return _jsonrpc_error(payload.get("id"), -32601, "Method not found", 400)


def _initialize_events(db) -> None:
    seeds = [
        ("seed-api-1", "payments-api", "info", "Payment authorization latency is within the synthetic baseline.", "2026-10-10T08:00:00Z"),
        ("seed-api-2", "payments-api", "warning", "Synthetic retry volume increased after a configuration rollout.", "2026-10-10T08:05:00Z"),
        ("seed-db-1", "ledger-db", "error", "Synthetic connection pool saturation caused delayed ledger writes.", "2026-10-10T08:12:00Z"),
        ("seed-auth-1", "identity-service", "info", "Token refresh health check completed successfully.", "2026-10-10T08:18:00Z"),
        ("seed-batch-1", "settlement-batch", "warning", "Synthetic settlement batch completed with a small retry backlog.", "2026-10-10T08:25:00Z"),
    ]
    with db.connect() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS runtime_events (id TEXT PRIMARY KEY, service TEXT NOT NULL, level TEXT NOT NULL, message TEXT NOT NULL, timestamp TEXT NOT NULL)")
        connection.execute("CREATE VIRTUAL TABLE IF NOT EXISTS runtime_events_fts USING fts5(event_id UNINDEXED, service, level, message, tokenize='unicode61')")
        for row in seeds:
            connection.execute("INSERT OR IGNORE INTO runtime_events(id,service,level,message,timestamp) VALUES(?,?,?,?,?)", row)
            connection.execute("INSERT INTO runtime_events_fts(event_id,service,level,message) SELECT ?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM runtime_events_fts WHERE event_id=?)", (*row[:4], row[0]))


def search_events(query: str, limit: int, config: dict[str, Any], db) -> dict[str, Any]:
    q = _clean_text(query, 300)
    limit = max(1, min(int(limit), 100))
    if config.get("es_url"):
        try:
            payload = {"size": limit, "sort": [{"timestamp": {"order": "desc", "unmapped_type": "date"}}], "query": {"multi_match": {"query": q, "fields": ["service", "level", "message"]}} if q else {"match_all": {}}}
            response = _es_request(config, "POST", f"/{PUBLIC_INDEX}/_search", payload)
            hits_section = response.get("hits") if isinstance(response, dict) else None
            hits_section = hits_section if isinstance(hits_section, dict) else {}
            hits = []
            for item in hits_section.get("hits", []):
                source = item.get("_source", {}) if isinstance(item, dict) else {}
                hits.append({"id": item.get("_id"), **{key: source.get(key, "") for key in ("service", "level", "message", "timestamp")}})
            total_raw = hits_section.get("total", 0)
            total = total_raw.get("value", 0) if isinstance(total_raw, dict) else total_raw
            return {"backend": "elasticsearch", "total": total, "hits": hits}
        except RuntimeError:
            raise
    with db.connect() as connection:
        if q:
            tokens = re.findall(r"[\w-]+", q)
            fts_query = " AND ".join('"' + token.replace('"', '""') + '"' for token in tokens)
            if not fts_query:
                return {"backend": "sqlite-fts5", "total": 0, "hits": []}
            total = connection.execute("SELECT COUNT(*) FROM runtime_events_fts WHERE runtime_events_fts MATCH ?", (fts_query,)).fetchone()[0]
            rows = connection.execute("SELECT e.* FROM runtime_events e JOIN runtime_events_fts f ON f.event_id=e.id WHERE runtime_events_fts MATCH ? ORDER BY e.timestamp DESC LIMIT ?", (fts_query, limit)).fetchall()
        else:
            total = connection.execute("SELECT COUNT(*) FROM runtime_events").fetchone()[0]
            rows = connection.execute("SELECT * FROM runtime_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return {"backend": "sqlite-fts5", "total": total, "hits": [dict(row) for row in rows]}


def dispatch_tool_call(active_skill: str, name: str, arguments: dict[str, Any], config: dict[str, Any], db) -> dict[str, Any]:
    if active_skill != ACTIVE_SKILL:
        raise PermissionError("skill_not_allowed")
    if name not in SKILL_TOOLS:
        raise PermissionError("tool_not_allowed")
    arguments = arguments if isinstance(arguments, dict) else {}
    if name == "es_search":
        index = arguments.get("index", PUBLIC_INDEX)
        if index not in {PUBLIC_INDEX, "demo-events", "public-ops-*"}:
            raise ValueError("Only the public runtime event index is available")
        query = arguments.get("query", "")
        return search_events(_clean_text(query, 300), min(int(arguments.get("size", 20)), 100), config, db)
    if name == "es_list_indices":
        if config.get("es_url"):
            result = _es_request(config, "GET", "/_cat/indices/public-ops-*", params={"format": "json", "h": "index,health,status,docs.count"})
            return {"backend": "elasticsearch", "indices": result if isinstance(result, list) else []}
        return {"backend": "sqlite-fts5", "indices": [PUBLIC_INDEX]}
    if name in {"es_get_mappings", "es_get_shards"}:
        index = arguments.get("index", PUBLIC_INDEX)
        if index != PUBLIC_INDEX:
            raise ValueError("Only the public runtime event index is available")
        if config.get("es_url"):
            path = f"/{quote(PUBLIC_INDEX, safe='')}/_mapping" if name == "es_get_mappings" else f"/{quote(PUBLIC_INDEX, safe='')}/_stats?level=shards"
            result = _es_request(config, "GET", path)
            return {"backend": "elasticsearch", "index": PUBLIC_INDEX, "data": result}
        if name == "es_get_mappings":
            return {"backend": "sqlite-fts5", "index": PUBLIC_INDEX, "fields": ["service", "level", "message", "timestamp"]}
        return {"backend": "sqlite-fts5", "index": PUBLIC_INDEX, "shards": [{"state": "local", "document_count": search_events("", 100, config, db)["total"]}]}
    raise PermissionError("tool_not_allowed")


def _es_request(config: dict[str, Any], method: str, path: str, body=None, params=None):
    base = config["es_url"].rstrip("/")
    try:
        response = requests.request(method, base + path, json=body, params=params, timeout=5, headers={"Accept": "application/json"})
        response.raise_for_status()
        return response.json() if response.content else {}
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("elasticsearch_unavailable") from exc


def _backend(config):
    return "elasticsearch" if config.get("es_url") else "sqlite-fts5"


def _tool_schema(name):
    props = {"es_search": {"index": {"type": "string"}, "query": {"type": "string"}, "size": {"type": "integer"}},
             "es_list_indices": {}, "es_get_mappings": {"index": {"type": "string"}}, "es_get_shards": {"index": {"type": "string"}}}[name]
    return {"type": "object", "properties": props, "additionalProperties": False}


def _clean_text(value, max_length):
    return value.strip()[:max_length] if isinstance(value, str) else ""


def _safe_error(value):
    return value if value in {"elasticsearch_unavailable"} else "The configured search provider failed."


def _provider_error(exc):
    return jsonify({"error": {"code": _safe_error(str(exc)), "message": "The configured search provider is unavailable."}}), 502


def _jsonrpc_error(request_id, code, message, status):
    return jsonify({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}), status
