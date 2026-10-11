"""Offline skill-scoped JSON-RPC MCP dispatch fixture."""
from __future__ import annotations

import json
from typing import Any


TOOLS: dict[str, dict[str, Any]] = {
    "es_search": {"description": "Search documents in a named index."},
    "es_esql": {"description": "Run an ES|QL query."},
    "es_list_indices": {"description": "List index names."},
    "es_get_mappings": {"description": "Read mappings for one exact index."},
    "es_get_shards": {"description": "Read shard allocation status."},
}

SKILL_CONFIG = {"es-dev-apm": ("es_search", "es_esql", "es_list_indices", "es_get_mappings", "es_get_shards")}
BACKEND_TOOL = {
    "es_search": "search", "es_esql": "esql", "es_list_indices": "list_indices",
    "es_get_mappings": "get_mappings", "es_get_shards": "get_shards",
}


class DispatchDenied(PermissionError):
    pass


class MockProvider:
    def __init__(self):
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        return {"fixture": "offline", "tool": name, "hits": [{"service.name": "demo-api"}]}


class SkillScopedMCP:
    def __init__(self, provider: MockProvider,
                 configuration: dict[str, tuple[str, ...] | None] | None):
        self.provider = provider
        self.configuration = configuration

    def tool_list(self, skill: str) -> list[dict[str, Any]]:
        if self.configuration is None or skill not in self.configuration or self.configuration[skill] is None:
            return []
        return [{"name": name, **TOOLS[name]} for name in self.configuration[skill] if name in TOOLS]

    def dispatch(self, skill: str, request: dict[str, Any]) -> dict[str, Any]:
        if request.get("jsonrpc") != "2.0" or request.get("method") != "tools/call":
            raise DispatchDenied("invalid JSON-RPC tools/call request")
        params = request.get("params")
        if not isinstance(params, dict) or not isinstance(params.get("name"), str):
            raise DispatchDenied("tool name is required")
        name = params["name"]
        allowed = {entry["name"] for entry in self.tool_list(skill)}
        if name not in allowed:
            raise DispatchDenied("tool is not enabled for this skill")
        args = params.get("arguments", {})
        if not isinstance(args, dict):
            raise DispatchDenied("arguments must be an object")
        result = self.provider.call(BACKEND_TOOL[name], args)
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"content": [
            {"type": "text", "text": json.dumps(result, sort_keys=True)}]}}


def demo() -> str:
    provider = MockProvider()
    server = SkillScopedMCP(provider, SKILL_CONFIG)
    request = {"jsonrpc": "2.0", "id": "demo-1", "method": "tools/call",
               "params": {"name": "es_search", "arguments": {"index": "fictional-apm", "query": "demo"}}}
    return json.dumps({"tools": [item["name"] for item in server.tool_list("es-dev-apm")],
                       "request": request, "response": server.dispatch("es-dev-apm", request),
                       "provider_calls": len(provider.calls), "external_connections": False}, indent=2)


if __name__ == "__main__":
    print(demo())
