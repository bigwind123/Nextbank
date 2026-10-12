from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
import re
import secrets
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from flask import Flask, abort, current_app, jsonify, request, send_file
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError


MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALLOWED_FORMATS = {"PNG", "JPEG"}
FIELD_LABELS = {
    "applicant_name": ("applicant", "applicant name", "name"),
    "income": ("monthly income", "income"),
    "account_number": ("account", "account number"),
}


def register_ocr(app: Flask, config: dict[str, Any], db) -> None:
    _initialize(db)
    key = _load_vault_key(Path(config["data_dir"]))
    app.extensions["portfolio_ocr_vault_key"] = key
    engine_lock = threading.Lock()
    engine = {"value": None}
    app.extensions["portfolio_ocr_mode"] = "rapidocr-cpu"

    @app.get("/api/ocr/cases")
    def ocr_cases_list():
        with db.connect() as connection:
            rows = connection.execute("SELECT id,title,state,created_at,updated_at FROM ocr_cases ORDER BY updated_at DESC").fetchall()
            counts = {row[0]: row[1] for row in connection.execute("SELECT case_id,COUNT(*) FROM ocr_documents GROUP BY case_id").fetchall()}
        return jsonify({"cases": [{**dict(row), "document_count": counts.get(row["id"], 0)} for row in rows]})

    @app.post("/api/ocr/cases")
    def ocr_cases_create():
        body = request.get_json(silent=True) or {}
        title = _clean(body.get("title"), 120) or "Untitled application"
        case_id, now = str(uuid.uuid4()), _now()
        with db.connect() as connection:
            connection.execute("INSERT INTO ocr_cases(id,title,state,created_at,updated_at) VALUES(?,?,?,?,?)", (case_id, title, "created", now, now))
        return jsonify({"case": _case_detail(case_id, db, key, config)}), 201

    @app.get("/api/ocr/cases/<case_id>")
    def ocr_case_detail(case_id):
        result = _case_detail(case_id, db, key, config)
        if result is None:
            abort(404)
        return jsonify({"case": result})

    @app.post("/api/ocr/cases/<case_id>/documents")
    def ocr_document_create(case_id):
        if _case_row(case_id, db) is None:
            abort(404)
        upload = request.files.get("file")
        if upload is None or not upload.filename:
            return _error("file_required", "Choose a PNG or JPEG image."), 400
        image_bytes = upload.stream.read(MAX_IMAGE_BYTES + 1)
        if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
            return _error("invalid_image_size", "The image must be between 1 byte and 8 MiB."), 413 if len(image_bytes) > MAX_IMAGE_BYTES else 400
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.format not in ALLOWED_FORMATS or image.width < 1 or image.height < 1 or image.width * image.height > 24_000_000:
                raise ValueError("unsupported image")
            image.verify()
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            return _error("invalid_image", "Upload a valid PNG or JPEG image."), 400
        provider = _clean(request.form.get("provider"), 20) or "rapidocr"
        if provider not in {"rapidocr", "vlm"}:
            return _error("unsupported_provider", "provider must be rapidocr or vlm."), 400
        try:
            if provider == "rapidocr":
                with engine_lock:
                    if engine["value"] is None:
                        from rapidocr import RapidOCR
                        engine["value"] = RapidOCR()
                    output = engine["value"](image)
                lines = list(output.txts or [])
                confidences = list(output.scores or [])
                recognized = "\n".join(str(line) for line in lines)
                fields, provenance = _extract_fields(lines, confidences)
            else:
                recognized, fields, provenance = _vision_recognize(image_bytes, config)
        except ProviderNotConfigured:
            return _error("provider_unconfigured", "Configure a vision model endpoint and model name to use VLM."), 503
        except ProviderFailure as exc:
            return _error("provider_error", f"The configured vision model request failed ({exc.code})."), 502
        document_id = str(uuid.uuid4())
        pseudonym = _pseudonym(key, case_id, document_id, fields.get("account_number"))
        payload = json.dumps({"ocr_text": recognized, "fields": fields, "provenance": provenance}, ensure_ascii=False).encode("utf-8")
        nonce = secrets.token_bytes(12)
        ciphertext = AESGCM(key).encrypt(nonce, payload, f"ocr-document:{case_id}:{document_id}".encode())
        filename = Path(upload.filename.replace("\\", "/")).name[:160] or "document"
        with db.connect() as connection:
            connection.execute("INSERT INTO ocr_documents(id,case_id,filename,provider,nonce,ciphertext,pseudonym,created_at) VALUES(?,?,?,?,?,?,?,?)", (document_id, case_id, filename, provider, nonce, ciphertext, pseudonym, _now()))
            # Any added evidence makes a prior assessment stale.
            connection.execute("UPDATE ocr_cases SET state='recognized',saved_response='',updated_at=? WHERE id=?", (_now(), case_id))
        notice = "The original image was sent to the configured vision model endpoint for recognition." if provider == "vlm" else None
        return jsonify({"case": _case_detail(case_id, db, key, config), "document": {"id": document_id, "filename": filename, "provider": provider, "status": "recognized", "ocr_text": recognized, "fields": fields, "provenance": provenance, "pseudonym": pseudonym}, "privacy_notice": notice}), 201

    @app.post("/api/ocr/cases/<case_id>/evaluate")
    def ocr_evaluate(case_id):
        case = _case_detail(case_id, db, key, config)
        if case is None:
            abort(404)
        body = request.get_json(silent=True) or {}
        mode = body.get("mode")
        if mode == "local-validation":
            response = _validate_case(case)
        elif mode == "llm":
            try:
                response = _llm_evaluate(case, config, key)
            except ProviderNotConfigured:
                return _error("provider_unconfigured", "Configure a model endpoint and model name to use LLM evaluation."), 503
            except ProviderFailure as exc:
                return _error("provider_error", f"The configured model request failed ({exc.code})."), 502
        else:
            return _error("invalid_mode", "mode must be local-validation or llm."), 400
        with db.connect() as connection:
            connection.execute("UPDATE ocr_cases SET state='evaluated',saved_response=?,updated_at=? WHERE id=?", (json.dumps(response, ensure_ascii=False), _now(), case_id))
        return jsonify({"case": _case_detail(case_id, db, key, config), "response": response})

    @app.get("/api/ocr/sample-document")
    def ocr_sample_document():
        image = Image.new("RGB", (1200, 420), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=38)
        lines = ["SYNTHETIC APPLICATION FORM", "Applicant: Jordan Lee", "Monthly Income: 76000", "Account Number: 31415926"]
        y = 24
        for line in lines:
            draw.text((36, y), line, fill="#17212b", font=font)
            y += 88
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        stream.seek(0)
        return send_file(stream, mimetype="image/png", download_name="synthetic-application.png")


class ProviderNotConfigured(Exception):
    pass


class ProviderFailure(Exception):
    def __init__(self, code: str):
        self.code = code


def _initialize(db):
    with db.connect() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS ocr_cases (id TEXT PRIMARY KEY,title TEXT NOT NULL,state TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,saved_response TEXT NOT NULL DEFAULT '')")
        connection.execute("CREATE TABLE IF NOT EXISTS ocr_documents (id TEXT PRIMARY KEY,case_id TEXT NOT NULL REFERENCES ocr_cases(id) ON DELETE CASCADE,filename TEXT NOT NULL,provider TEXT NOT NULL,nonce BLOB NOT NULL,ciphertext BLOB NOT NULL,pseudonym TEXT NOT NULL,created_at TEXT NOT NULL)")
        connection.execute("CREATE INDEX IF NOT EXISTS ocr_documents_case_idx ON ocr_documents(case_id,created_at)")


def _load_vault_key(data_dir: Path) -> bytes:
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "ocr-vault.key"
    if path.is_file():
        key = path.read_bytes()
        if len(key) != 32:
            raise RuntimeError("Local OCR vault key is invalid")
        return key
    key = AESGCM.generate_key(bit_length=256)
    try:
        with path.open("xb") as stream:
            stream.write(key)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    except FileExistsError:
        key = path.read_bytes()
    if len(key) != 32:
        raise RuntimeError("Local OCR vault key is invalid")
    return key


def _case_row(case_id, db):
    with db.connect() as connection:
        row = connection.execute("SELECT * FROM ocr_cases WHERE id=?", (case_id,)).fetchone()
    return row


def _case_detail(case_id, db, key, config):
    with db.connect() as connection:
        row = connection.execute("SELECT * FROM ocr_cases WHERE id=?", (case_id,)).fetchone()
        if row is None:
            return None
        docs = connection.execute("SELECT * FROM ocr_documents WHERE case_id=? ORDER BY created_at", (case_id,)).fetchall()
    documents = []
    for doc in docs:
        payload = AESGCM(key).decrypt(doc["nonce"], doc["ciphertext"], f"ocr-document:{case_id}:{doc['id']}".encode())
        decoded = json.loads(payload.decode("utf-8"))
        documents.append({"id": doc["id"], "filename": doc["filename"], "provider": doc["provider"], "status": "recognized", "ocr_text": decoded["ocr_text"], "fields": decoded["fields"], "provenance": decoded["provenance"], "pseudonym": doc["pseudonym"], "created_at": doc["created_at"]})
    saved = json.loads(row["saved_response"]) if row["saved_response"] else None
    configured = bool(_has_model(config))
    preview_records = _outbound_evaluation_records({"id": case_id, "documents": documents}, key) if documents else []
    return {
        "id": row["id"], "title": row["title"], "state": row["state"], "created_at": row["created_at"], "updated_at": row["updated_at"],
        "documents": documents, "next_request": _next_request(documents, saved), "saved_response": saved,
        "outbound_payload_preview": {
            "model": config.get("model_name") if configured else None,
            "records": preview_records,
            "includes_raw_image": False,
            "includes_raw_ocr_text": False,
        },
        "parser": {"stage": "recognized" if documents else "waiting_for_document", "validation_available": bool(documents), "llm_configured": configured},
    }


def _next_request(documents, saved):
    if not documents:
        return "Upload a PNG or JPEG application image to start recognition."
    if saved is None:
        return "Review the extracted fields, then run local schema validation or configured LLM evaluation."
    return "Review the saved evaluation and correct any source document details if needed."


def _extract_fields(lines, scores):
    fields = {}
    provenance = {}
    for index, raw in enumerate(lines):
        text = str(raw).strip()
        folded = text.casefold()
        for field, labels in FIELD_LABELS.items():
            label = next((label for label in labels if label in folded), None)
            if not label or field in fields:
                continue
            value = text
            if ":" in text:
                value = text.split(":", 1)[1].strip()
            else:
                value = re.sub(re.escape(label), "", text, count=1, flags=re.IGNORECASE).strip(" :-")
            if field == "income":
                normalized = value.strip()
                if re.fullmatch(r"\+?(?:\d+|\d{1,3}(?:,\d{3})+)", normalized):
                    value = int(normalized.replace(",", "").lstrip("+"))
                else:
                    value = None
            elif field == "account_number":
                value = re.sub(r"\s+", "", value)
            if value not in {None, ""}:
                fields[field] = value
                provenance[field] = {"line_index": index, "source_text": text[:300], "confidence": round(float(scores[index]), 5) if index < len(scores) else None}
    return fields, provenance


def _vision_recognize(image_bytes, config):
    model = config.get("vision_model_name", "")
    base = config.get("model_base_url", "")
    if not model or not base:
        raise ProviderNotConfigured()
    data = base64.b64encode(image_bytes).decode("ascii")
    mime = "image/jpeg" if image_bytes[:3] == b"\xff\xd8\xff" else "image/png"
    response = _chat_completion(config, model, [{"role": "user", "content": [
        {"type": "text", "text": "Read this synthetic application image. Return JSON with ocr_text, applicant_name, income, account_number. Include only visible text and use null for missing fields."},
        {"type": "image_url", "image_url": {"url": f"data:{mime};base64," + data}},
    ]}], json_mode=True)
    try:
        content = response["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        allowed = {}
        for name in ("applicant_name", "income", "account_number"):
            value = parsed.get(name)
            if isinstance(value, (str, int, float)) and not isinstance(value, bool) and value != "":
                allowed[name] = value
        text = _clean(parsed.get("ocr_text"), 8000)
        provenance = {field: {"source": "configured_vlm", "confidence": None} for field in allowed}
        return text, allowed, provenance
    except (KeyError, IndexError, TypeError, json.JSONDecodeError, AttributeError) as exc:
        raise ProviderFailure("invalid_response") from exc


def _llm_evaluate(case, config, key):
    model = config.get("model_name", "")
    if not model or not config.get("model_base_url"):
        raise ProviderNotConfigured()
    records = _outbound_evaluation_records(case, key)
    prompt = "Evaluate only schema presence and formats in these recognized application fields. Do not recalculate income or infer eligibility. Return JSON with status, field_checks, and explanation. Input: " + json.dumps(records, ensure_ascii=False)
    response = _chat_completion(config, model, [{"role": "user", "content": prompt}], json_mode=True)
    try:
        return {"mode": "llm", "model": model, "result": json.loads(response["choices"][0]["message"]["content"])}
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise ProviderFailure("invalid_response") from exc


def _chat_completion(config, model, messages, json_mode=False, tools=None):
    url = config.get("model_base_url", "").rstrip("/")
    if not url:
        raise ProviderNotConfigured()
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    payload = {"model": model, "messages": messages}
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    token = os.environ.get("PORTFOLIO_MODEL_API_KEY") or config.get("model_api_key") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        parsed = response.json()
        if not isinstance(parsed, dict):
            raise ValueError()
        return parsed
    except (requests.RequestException, ValueError) as exc:
        raise ProviderFailure("unavailable") from exc


def _validate_case(case):
    fields = {}
    for document in case["documents"]:
        fields.update(document["fields"])
    checks = {
        "applicant_name": {"present": bool(isinstance(fields.get("applicant_name"), str) and fields["applicant_name"].strip()), "schema": "non-empty string"},
        "income": {"present": isinstance(fields.get("income"), int) and not isinstance(fields.get("income"), bool) and fields["income"] >= 0, "schema": "non-negative integer"},
        "account_number": {"present": bool(isinstance(fields.get("account_number"), str) and re.fullmatch(r"[A-Za-z0-9-]{4,32}", fields["account_number"])), "schema": "4 to 32 letters, digits, or hyphens"},
    }
    status = "valid" if all(item["present"] for item in checks.values()) else "needs_review"
    return {"mode": "local-validation", "status": status, "field_checks": checks, "message": "Local schema validation only; no financial formula or eligibility model was run."}


def _pseudonym(key, case_id, document_id, account):
    if not account:
        return "account_unavailable"
    hmac_key = hmac.new(key, b"portfolio-ocr-pseudonym-v1", hashlib.sha256).digest()
    value = f"{case_id}:{document_id}:{account}".encode("utf-8")
    return "acct_" + hmac.new(hmac_key, value, hashlib.sha256).hexdigest()[:16]


def _outbound_evaluation_records(case, key):
    """Build a flat, de-identified model profile without source text or IDs."""
    protected = {"applicant_name": "person", "account_number": "account"}
    records = []
    for document in case["documents"]:
        profile = {}
        fields = document.get("fields", {})
        for field in ("applicant_name", "income", "account_number"):
            value = fields.get(field)
            if field in protected and isinstance(value, str) and value:
                scoped = f"{case['id']}:{document['id']}:{field}:{value}".encode("utf-8")
                token = hmac.new(key, b"portfolio-ocr-outbound-v1:" + scoped, hashlib.sha256).hexdigest()[:32]
                profile[field] = f"{protected[field]}_{token}"
            elif field == "income" and isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                profile[field] = value
        # Keep only field names as provenance. Source line text and raw OCR text
        # are intentionally stored locally and never included in model input.
        records.append({"profile": profile, "provenance": {"recognized_fields": sorted(profile)}})
    return records


def _has_model(config, allow_empty=False):
    return bool(config.get("model_base_url") and config.get("model_name")) if config else allow_empty


def _clean(value, max_length):
    return value.strip()[:max_length] if isinstance(value, str) else ""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _error(code, message):
    return jsonify({"error": {"code": code, "message": message}})
