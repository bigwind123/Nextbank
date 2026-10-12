from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from flask import Flask, abort, jsonify, request, Response

from .mcp import ACTIVE_SKILL, SKILL_TOOLS, dispatch_tool_call
from .ocr import ProviderFailure, ProviderNotConfigured, _chat_completion


def register_chat(app: Flask, config: dict[str, Any], db) -> None:
    _initialize(db)
    app.extensions["portfolio_chat_mode"] = "configured-model" if config.get("model_base_url") and config.get("model_name") else "search-only"

    @app.get("/api/chat/rooms")
    def rooms_list():
        with db.connect() as connection:
            rows = connection.execute("SELECT r.id,r.title,r.created_at,r.updated_at,COUNT(m.id) AS message_count FROM chat_rooms r LEFT JOIN chat_messages m ON m.room_id=r.id GROUP BY r.id ORDER BY r.updated_at DESC").fetchall()
        return jsonify({"rooms": [dict(row) for row in rows]})

    @app.post("/api/chat/rooms")
    def rooms_create():
        body = request.get_json(silent=True) or {}
        title = _clean(body.get("title"), 120) or "Operations chat"
        room_id, now = str(uuid.uuid4()), _now()
        with db.connect() as connection:
            connection.execute("INSERT INTO chat_rooms(id,title,created_at,updated_at) VALUES(?,?,?,?)", (room_id,title,now,now))
        return jsonify({"room": _room_detail(room_id, db)}), 201

    @app.get("/api/chat/rooms/<room_id>")
    def room_detail(room_id):
        room = _room_detail(room_id, db)
        if room is None:
            abort(404)
        return jsonify({"room": room})

    @app.post("/api/chat/rooms/<room_id>/messages")
    def messages_create(room_id):
        room = _room_detail(room_id, db)
        if room is None:
            abort(404)
        body = request.get_json(silent=True) or {}
        message = _clean(body.get("message"), 8000)
        mode = body.get("mode", "search")
        if not message:
            return _error("message_required", "Enter a message."), 400
        if mode not in {"search", "llm"}:
            return _error("invalid_mode", "mode must be search or llm."), 400
        if mode == "llm" and not (config.get("model_base_url") and config.get("model_name")):
            return _error("provider_unconfigured", "Configure a model endpoint and model name to use LLM chat."), 503
        user_message = _save_message(db, room_id, "user", message, mode)
        if mode == "search":
            try:
                result = dispatch_tool_call(ACTIVE_SKILL, "es_search", {"index": "public-ops-events", "query": message, "size": 20}, config, db)
            except (RuntimeError, ValueError) as exc:
                return _search_error(exc)
            toolcall = _save_toolcall(db, room_id, "es_search", {"query": message}, result)
            answer = {"kind": "search-results", "backend": result["backend"], "total": result["total"], "hits": result["hits"]}
            assistant_message = _save_message(db, room_id, "assistant", json.dumps(answer, ensure_ascii=False), "search", answer)
            return jsonify({"message": assistant_message, "toolcalls": [toolcall], "room": _room_detail(room_id, db)}), 201
        try:
            assistant_text, toolcalls = _run_llm(room_id, message, db, config)
        except ProviderNotConfigured:
            return _error("provider_unconfigured", "Configure a model endpoint and model name to use LLM chat."), 503
        except ProviderFailure as exc:
            return _error("provider_error", f"The configured model request failed ({exc.code})."), 502
        except PermissionError:
            return _error("tool_not_allowed", "The model requested a tool outside the active skill."), 403
        assistant_message = _save_message(db, room_id, "assistant", assistant_text, "llm")
        return jsonify({"message": assistant_message, "toolcalls": toolcalls, "room": _room_detail(room_id, db)}), 201

    @app.delete("/api/chat/rooms/<room_id>/messages")
    def messages_clear(room_id):
        if _room_row(room_id, db) is None:
            abort(404)
        with db.connect() as connection:
            connection.execute("DELETE FROM chat_toolcalls WHERE room_id=?", (room_id,))
            connection.execute("DELETE FROM chat_messages WHERE room_id=?", (room_id,))
            connection.execute("UPDATE chat_rooms SET updated_at=? WHERE id=?", (_now(), room_id))
        return jsonify({"room": _room_detail(room_id, db)})

    @app.get("/api/chat/rooms/<room_id>/export")
    def room_export(room_id):
        room = _room_detail(room_id, db)
        if room is None:
            abort(404)
        lines = [f"{room['title']}", ""]
        for message in room["messages"]:
            lines.extend([f"[{message['created_at']}] {message['role']}", message["content"], ""])
        return Response("\n".join(lines), mimetype="text/plain; charset=utf-8", headers={"Content-Disposition": f"attachment; filename=chat-{room_id}.txt"})


def _initialize(db):
    with db.connect() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS chat_rooms(id TEXT PRIMARY KEY,title TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS chat_messages(id TEXT PRIMARY KEY,room_id TEXT NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,role TEXT NOT NULL,content TEXT NOT NULL,mode TEXT NOT NULL,metadata_json TEXT NOT NULL DEFAULT '{}',created_at TEXT NOT NULL)")
        connection.execute("CREATE TABLE IF NOT EXISTS chat_toolcalls(id TEXT PRIMARY KEY,room_id TEXT NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,name TEXT NOT NULL,arguments_json TEXT NOT NULL,result_json TEXT NOT NULL,created_at TEXT NOT NULL)")
        connection.execute("CREATE INDEX IF NOT EXISTS chat_messages_room_idx ON chat_messages(room_id,created_at)")


def _run_llm(room_id, latest, db, config):
    with db.connect() as connection:
        previous = connection.execute("SELECT role,content,metadata_json FROM chat_messages WHERE room_id=? ORDER BY created_at", (room_id,)).fetchall()
    messages = [{"role": "system", "content": "You help inspect synthetic public operations events. Use es_search for operational facts, cite only returned results, and say when none are found. Do not claim access outside the active elasticsearch-ops skill."}]
    for row in previous:
        item = {"role": row["role"], "content": row["content"]}
        metadata = json.loads(row["metadata_json"])
        if row["role"] == "assistant" and metadata.get("tool_calls"):
            item["tool_calls"] = metadata["tool_calls"]
        messages.append(item)
    tools = [{"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "index": {"type": "string"}, "size": {"type": "integer"}}, "additionalProperties": False}}} for name, description in SKILL_TOOLS.items() if name == "es_search"]
    calls_recorded = []
    for _ in range(3):
        response = _chat_completion(config, config["model_name"], messages, tools=tools)
        try:
            assistant = response["choices"][0]["message"]
            text = assistant.get("content") or ""
            calls = assistant.get("tool_calls") or []
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderFailure("invalid_response") from exc
        if not calls:
            if not text:
                raise ProviderFailure("empty_response")
            if messages and messages[-1].get("role") == "user":
                pass
            return text[:12000], calls_recorded
        messages.append({"role": "assistant", "content": text or None, "tool_calls": calls})
        for call in calls:
            function = call.get("function", {}) if isinstance(call, dict) else {}
            name = function.get("name")
            if name not in SKILL_TOOLS or name != "es_search":
                raise PermissionError("tool_not_allowed")
            try:
                arguments = json.loads(function.get("arguments") or "{}")
            except json.JSONDecodeError as exc:
                raise ProviderFailure("invalid_tool_arguments") from exc
            try:
                result = dispatch_tool_call(ACTIVE_SKILL, name, arguments, config, db)
            except PermissionError:
                raise
            except (RuntimeError, ValueError) as exc:
                raise ProviderFailure("search_unavailable") from exc
            row = _save_toolcall(db, room_id, name, arguments, result)
            calls_recorded.append(row)
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "content": json.dumps(result, ensure_ascii=False)})
    raise ProviderFailure("tool_call_limit")


def _save_message(db, room_id, role, content, mode, metadata=None):
    msg_id, now = str(uuid.uuid4()), _now()
    with db.connect() as connection:
        connection.execute("INSERT INTO chat_messages(id,room_id,role,content,mode,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)", (msg_id, room_id, role, content, mode, json.dumps(metadata or {}, ensure_ascii=False), now))
        connection.execute("UPDATE chat_rooms SET updated_at=? WHERE id=?", (now, room_id))
    return {"id": msg_id, "room_id": room_id, "role": role, "content": content, "mode": mode, "metadata": metadata or {}, "created_at": now}


def _save_toolcall(db, room_id, name, arguments, result):
    tool_id, now = str(uuid.uuid4()), _now()
    with db.connect() as connection:
        connection.execute("INSERT INTO chat_toolcalls(id,room_id,name,arguments_json,result_json,created_at) VALUES(?,?,?,?,?,?)", (tool_id, room_id, name, json.dumps(arguments, ensure_ascii=False), json.dumps(result, ensure_ascii=False), now))
    return {"id": tool_id, "name": name, "arguments": arguments, "result": result, "created_at": now}


def _room_detail(room_id, db):
    with db.connect() as connection:
        room = connection.execute("SELECT * FROM chat_rooms WHERE id=?", (room_id,)).fetchone()
        if room is None:
            return None
        messages = connection.execute("SELECT * FROM chat_messages WHERE room_id=? ORDER BY created_at", (room_id,)).fetchall()
        calls = connection.execute("SELECT * FROM chat_toolcalls WHERE room_id=? ORDER BY created_at", (room_id,)).fetchall()
    return {**dict(room), "messages": [{"id": row["id"], "room_id": row["room_id"], "role": row["role"], "content": row["content"], "mode": row["mode"], "metadata": json.loads(row["metadata_json"]), "created_at": row["created_at"]} for row in messages], "toolcalls": [{"id": row["id"], "name": row["name"], "arguments": json.loads(row["arguments_json"]), "result": json.loads(row["result_json"]), "created_at": row["created_at"]} for row in calls]}


def _room_row(room_id, db):
    with db.connect() as connection:
        return connection.execute("SELECT id FROM chat_rooms WHERE id=?", (room_id,)).fetchone()


def _search_error(exc):
    message = "The configured search provider is unavailable." if str(exc) == "elasticsearch_unavailable" else "The search request could not be completed."
    return _error("search_provider_error", message), 502


def _error(code, message):
    return jsonify({"error": {"code": code, "message": message}})


def _clean(value, length):
    return value.strip()[:length] if isinstance(value, str) else ""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
