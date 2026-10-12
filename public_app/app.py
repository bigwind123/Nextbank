from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from .config import PROJECT_ROOT, load_config
from .db import Database
from .gateway import _provider_for_config, register_gateway


APP_FILES = {"app.html", "app.en.html", "index.html", "demo.html", "demo.en.html"}
PUBLIC_ROOT_FILES = APP_FILES | {
    "README.md", "README.zh-TW.md", "CONTENT_SELECTION.md", "THIRD_PARTY_NOTICES.md",
    "examples/README.md", "examples/SCENARIOS.md",
}
ASSET_FILES = {
    "assets/portfolio.css",
    "assets/demo.css",
    "assets/demo.js",
    "assets/app.css",
    "assets/app.js",
    "assets/runtime.css",
    "assets/runtime.js",
}
PUBLIC_DIRECTORY_EXTENSIONS = {
    "docs": {".md"},
    "case-studies": {".md"},
    "assets/diagrams": {".html", ".svg", ".json"},
    "assets/screenshots": {".png"},
}
LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _authority(value: str, scheme: str) -> tuple[str, int] | None:
    try:
        parsed = urlsplit("//" + value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None
    if (not hostname or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment
            or hostname.lower() not in LOOPBACK_HOSTS):
        return None
    if port is None:
        port = 443 if scheme == "https" else 80
    return hostname.lower(), port


def _local_request_guard():
    path = request.path
    if path != "/api" and not path.startswith("/api/") and path != "/mcp":
        return None
    host_header = request.headers.get("Host", "")
    host = _authority(host_header, request.scheme)
    if not host:
        return jsonify({"error": {"code": "invalid_host", "message": "This local API accepts loopback Host values only."}}), 403
    if "Origin" in request.headers:
        origin_value = request.headers.get("Origin", "")
        try:
            origin = urlsplit(origin_value)
        except ValueError:
            origin = None
        if (origin is None or origin.scheme not in {"http", "https"} or not origin.netloc
                or origin.path not in {"", "/"} or origin.query or origin.fragment
                or origin.username or origin.password or origin.scheme != request.scheme):
            return jsonify({"error": {"code": "origin_forbidden", "message": "This local API accepts same-origin requests only."}}), 403
        origin_authority = _authority(origin.netloc, origin.scheme)
        if not origin_authority or origin_authority != host:
            return jsonify({"error": {"code": "origin_forbidden", "message": "This local API accepts same-origin requests only."}}), 403
    return None


def create_app(config: dict[str, Any] | None = None, *, database: Database | None = None) -> Flask:
    runtime_config = load_config(config)
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = 9 * 1024 * 1024
    app.config["PORTFOLIO_CONFIG"] = runtime_config
    # Register first so no API or MCP route can mutate state before this guard.
    app.before_request(_local_request_guard)
    db = database or Database(Path(runtime_config["data_dir"]) / "portfolio.sqlite3")
    with db.connect() as connection:
        saved_settings = connection.execute("SELECT name, value FROM runtime_settings").fetchall()
    for row in saved_settings:
        if row["name"] in {"model_base_url", "model_name", "vision_model_name", "es_url", "litellm_url"}:
            runtime_config[row["name"]] = row["value"]
    app.extensions["portfolio_database"] = db
    provider, provider_mode = _provider_for_config(runtime_config, db)
    app.extensions["portfolio_gateway_provider"] = provider
    app.extensions["portfolio_gateway_provider_mode"] = provider_mode
    app.extensions["portfolio_modules"] = {"gateway": True, "ocr": False, "chat": False, "mcp": False}
    register_gateway(app, runtime_config, db)
    _register_optional_modules(app, runtime_config, db)

    @app.after_request
    def no_cache_html(response):
        if response.mimetype in {"text/html", "application/javascript", "text/css"}:
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error: HTTPException):
        return jsonify({"error": {"code": error.name.lower().replace(" ", "_"), "message": error.description}}), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error: Exception):
        # Avoid leaking provider response bodies, credentials, or config in the API response.
        app.logger.error("Unhandled local runtime error: %s", type(error).__name__)
        return jsonify({"error": {"code": "internal_error", "message": "The local runtime could not complete this request."}}), 500

    @app.get("/")
    def home():
        if not (PROJECT_ROOT / "app.html").is_file():
            return jsonify({"error": {"code": "frontend_not_installed", "message": "The runtime frontend is not present in this checkout."}}), 503
        return send_from_directory(PROJECT_ROOT, "app.html")

    @app.get("/app.html")
    def home_explicit():
        return _serve_public_file("app.html")

    @app.get("/app.en.html")
    def home_english():
        return _serve_public_file("app.en.html")

    @app.get("/portfolio")
    def portfolio_home():
        return _serve_public_file("index.html")

    @app.get("/demo.html")
    def demo_zh():
        return _serve_public_file("demo.html")

    @app.get("/demo.en.html")
    def demo_en():
        return _serve_public_file("demo.en.html")

    @app.get("/assets/<path:asset_name>")
    def public_asset(asset_name: str):
        normalized = "assets/" + asset_name.replace("\\", "/")
        return _serve_public_path(normalized)

    @app.get("/<path:public_path>")
    def public_document(public_path: str):
        return _serve_public_path(public_path)

    return app


def _serve_public_file(name: str):
    if name not in APP_FILES:
        abort(404)
    path = PROJECT_ROOT / name
    if not path.is_file():
        return jsonify({"error": {"code": "frontend_not_installed", "message": "The requested local page is not present in this checkout."}}), 404
    return send_from_directory(PROJECT_ROOT, name)


def _serve_public_path(relative_path: str):
    normalized = relative_path.replace("\\", "/")
    parts = normalized.split("/")
    if (not normalized or normalized.startswith("/") or any(part in {"", ".", ".."} or part.startswith(".") for part in parts)):
        abort(404)
    candidate = PROJECT_ROOT / Path(*parts)
    try:
        resolved = candidate.resolve(strict=True)
        root = PROJECT_ROOT.resolve(strict=True)
        canonical = resolved.relative_to(root).as_posix()
    except (OSError, ValueError):
        abort(404)
    if not resolved.is_file():
        abort(404)
    allowed = canonical in PUBLIC_ROOT_FILES or canonical in ASSET_FILES or canonical == "third_party/ARCHIFY_LICENSE"
    for public_dir, extensions in PUBLIC_DIRECTORY_EXTENSIONS.items():
        if canonical.startswith(public_dir + "/") and Path(canonical).suffix.lower() in extensions:
            allowed = True
            break
    if not allowed:
        abort(404)
    return send_from_directory(root, canonical)


def _register_optional_modules(app: Flask, config: dict[str, Any], db: Database) -> None:
    # OCR/chat/MCP modules can be added independently without making the core
    # Gateway depend on inference packages or an Elasticsearch client.
    modules = (
        ("public_app.ocr", "register_ocr", "ocr"),
        ("public_app.chat", "register_chat", "chat"),
        ("public_app.mcp", "register_mcp", "mcp"),
    )
    for module_name, register_name, capability in modules:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            if exc.name == module_name:
                continue
            raise
        register = getattr(module, register_name, None)
        if not callable(register):
            raise RuntimeError(f"Optional module {module_name} does not implement {register_name}(app, config, db)")
        register(app, config, db)
        app.extensions["portfolio_modules"][capability] = True
        app.extensions.setdefault(f"portfolio_{capability}_mode", "fixture")
