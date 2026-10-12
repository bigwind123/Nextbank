from __future__ import annotations

import io
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from public_app import create_app


def document_image(lines: list[str]) -> bytes:
    image = Image.new("RGB", (1250, 440), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=42)
    for index, text in enumerate(lines):
        draw.text((35, 25 + index * 96), text, fill="black", font=font)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


class RuntimeIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({"data_dir": self.temp.name, "model_base_url": "", "model_name": "", "vision_model_name": "", "es_url": ""})
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_rapidocr_reads_two_different_uploaded_images_and_vault_survives_restart(self):
        case = self.client.post("/api/ocr/cases", json={"title": "Synthetic application A"}).get_json()["case"]
        first_bytes = document_image(["Applicant: MAYA LIN", "Monthly Income: 82000", "Account Number: 12345678"])
        second_bytes = document_image(["Applicant: ELI WONG", "Monthly Income: 64000", "Account Number: 99887766"])
        first = self.client.post(f"/api/ocr/cases/{case['id']}/documents", data={"file": (io.BytesIO(first_bytes), "maya.png"), "provider": "rapidocr"}, content_type="multipart/form-data")
        second = self.client.post(f"/api/ocr/cases/{case['id']}/documents", data={"file": (io.BytesIO(second_bytes), "eli.png"), "provider": "rapidocr"}, content_type="multipart/form-data")
        self.assertEqual(first.status_code, 201, first.get_json())
        self.assertEqual(second.status_code, 201, second.get_json())
        first_doc = first.get_json()["document"]
        second_doc = second.get_json()["document"]
        self.assertIn("MAYA LIN", first_doc["ocr_text"])
        self.assertIn("ELI WONG", second_doc["ocr_text"])
        self.assertNotEqual(first_doc["ocr_text"], second_doc["ocr_text"])
        self.assertEqual(first_doc["fields"]["applicant_name"], "MAYA LIN")
        self.assertEqual(first_doc["fields"]["income"], 82000)
        self.assertEqual(first_doc["fields"]["account_number"], "12345678")
        self.assertNotEqual(first_doc["pseudonym"], second_doc["pseudonym"])
        db = self.app.extensions["portfolio_database"]
        with db.connect() as connection:
            raw_doc = connection.execute("SELECT ciphertext FROM ocr_documents WHERE id=?", (first_doc["id"],)).fetchone()[0]
            self.assertNotIn(b"MAYA LIN", raw_doc)
            self.assertNotIn(b"12345678", raw_doc)
        validation = self.client.post(f"/api/ocr/cases/{case['id']}/evaluate", json={"mode": "local-validation"}).get_json()["response"]
        self.assertEqual(validation["mode"], "local-validation")
        self.assertIn("no financial formula", validation["message"])
        restarted = create_app({"data_dir": self.temp.name, "model_base_url": "", "model_name": "", "es_url": ""})
        case_after_restart = restarted.test_client().get(f"/api/ocr/cases/{case['id']}").get_json()["case"]
        self.assertEqual(case_after_restart["documents"][0]["fields"]["applicant_name"], "MAYA LIN")
        self.assertEqual(case_after_restart["saved_response"]["mode"], "local-validation")

    def test_llm_evaluation_sends_only_deidentified_flat_profile_and_restart_restores_local_fields(self):
        captured = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                captured.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                content = json.dumps({"status": "review", "field_checks": {}, "explanation": "synthetic"})
                body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            app = create_app({
                "data_dir": self.temp.name,
                "model_base_url": f"http://127.0.0.1:{server.server_port}/v1",
                "model_name": "local-review-model",
                "litellm_management_api_key": "management-secret-must-not-be-used-for-inference",
            })
            client = app.test_client()
            case = client.post("/api/ocr/cases", json={"title": "synthetic protected profile"}).get_json()["case"]
            upload = client.post(
                f"/api/ocr/cases/{case['id']}/documents",
                data={"file": (io.BytesIO(document_image(["Applicant: MAYA LIN", "Monthly Income: 82,000", "Account Number: 12345678"])), "synthetic.png"), "provider": "rapidocr"},
                content_type="multipart/form-data",
            )
            self.assertEqual(upload.status_code, 201, upload.get_json())
            preview = upload.get_json()["case"]["outbound_payload_preview"]
            self.assertFalse(preview["includes_raw_image"])
            self.assertFalse(preview["includes_raw_ocr_text"])
            self.assertNotIn("MAYA LIN", json.dumps(preview))
            self.assertNotIn("12345678", json.dumps(preview))
            evaluation = client.post(f"/api/ocr/cases/{case['id']}/evaluate", json={"mode": "llm"})
            self.assertEqual(evaluation.status_code, 200, evaluation.get_json())
            outbound = json.dumps(captured[0], ensure_ascii=False)
            prompt = captured[0]["messages"][0]["content"]
            sent_profile = json.loads(prompt.split("Input: ", 1)[1])[0]["profile"]
            self.assertNotIn("MAYA LIN", outbound)
            self.assertNotIn("12345678", outbound)
            self.assertNotIn("source_text", outbound)
            for raw_line in ("Applicant: MAYA LIN", "Monthly Income: 82,000", "Account Number: 12345678"):
                self.assertNotIn(raw_line, outbound)
            self.assertEqual(sent_profile["income"], 82000)
            self.assertTrue(sent_profile["applicant_name"].startswith("person_"))
            self.assertTrue(sent_profile["account_number"].startswith("account_"))
            self.assertEqual(preview["records"][0]["profile"], sent_profile)
            self.assertNotIn("management-secret-must-not-be-used-for-inference", outbound)

            restarted = create_app({"data_dir": self.temp.name})
            restored = restarted.test_client().get(f"/api/ocr/cases/{case['id']}").get_json()["case"]
            self.assertEqual(restored["documents"][0]["fields"]["applicant_name"], "MAYA LIN")
            self.assertEqual(restored["documents"][0]["fields"]["account_number"], "12345678")
            self.assertIsNotNone(restored["saved_response"])
            self.assertEqual(restored["outbound_payload_preview"]["records"], preview["records"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_vlm_response_discloses_original_image_transfer_to_configured_endpoint(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                content = json.dumps({"ocr_text": "Synthetic", "applicant_name": "TAYLOR PARK", "income": 0, "account_number": "ABC12345"})
                body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            app = create_app({
                "data_dir": self.temp.name,
                "model_base_url": f"http://127.0.0.1:{server.server_port}/v1",
                "vision_model_name": "local-vision-model",
            })
            client = app.test_client()
            case = client.post("/api/ocr/cases", json={}).get_json()["case"]
            response = client.post(
                f"/api/ocr/cases/{case['id']}/documents",
                data={"file": (io.BytesIO(document_image(["Applicant: TAYLOR PARK"])), "synthetic.png"), "provider": "vlm"},
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 201, response.get_json())
            self.assertIn("original image was sent to the configured vision model endpoint", response.get_json()["privacy_notice"])
            self.assertIn("data:image/png;base64,", seen[0]["messages"][0]["content"][1]["image_url"]["url"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_adding_document_invalidates_saved_evaluation_and_amount_parser_rejects_negative_or_decimal(self):
        from public_app.ocr import _extract_fields, _validate_case

        parsed, _ = _extract_fields(["Monthly Income: -1200"], [0.99])
        self.assertNotIn("income", parsed)
        parsed, _ = _extract_fields(["Monthly Income: 12.50"], [0.99])
        self.assertNotIn("income", parsed)
        invalid = {"documents": [{"fields": {"applicant_name": "Synthetic", "income": -1, "account_number": "ABC12345"}}]}
        self.assertFalse(_validate_case(invalid)["field_checks"]["income"]["present"])

        case = self.client.post("/api/ocr/cases", json={}).get_json()["case"]
        first = self.client.post(
            f"/api/ocr/cases/{case['id']}/documents",
            data={"file": (io.BytesIO(document_image(["Applicant: DEVON TEST", "Monthly Income: 0", "Account Number: 10000001"])), "one.png"), "provider": "rapidocr"},
            content_type="multipart/form-data",
        )
        self.assertEqual(first.status_code, 201, first.get_json())
        evaluated = self.client.post(f"/api/ocr/cases/{case['id']}/evaluate", json={"mode": "local-validation"})
        self.assertIsNotNone(evaluated.get_json()["case"]["saved_response"])
        second = self.client.post(
            f"/api/ocr/cases/{case['id']}/documents",
            data={"file": (io.BytesIO(document_image(["Applicant: OTHER TEST", "Monthly Income: 0", "Account Number: 10000002"])), "two.png"), "provider": "rapidocr"},
            content_type="multipart/form-data",
        )
        self.assertEqual(second.status_code, 201, second.get_json())
        current = self.client.get(f"/api/ocr/cases/{case['id']}").get_json()["case"]
        self.assertIsNone(current["saved_response"])
        self.assertEqual(current["state"], "recognized")

    def test_missing_model_has_explicit_503_for_llm_and_vlm(self):
        room = self.client.post("/api/chat/rooms", json={}).get_json()["room"]
        llm = self.client.post(f"/api/chat/rooms/{room['id']}/messages", json={"message": "check events", "mode": "llm"})
        self.assertEqual(llm.status_code, 503)
        self.assertEqual(llm.get_json()["error"]["code"], "provider_unconfigured")
        case = self.client.post("/api/ocr/cases", json={}).get_json()["case"]
        response = self.client.post(f"/api/ocr/cases/{case['id']}/documents", data={"file": (io.BytesIO(document_image(["Applicant: TAYLOR PARK"])), "sample.png"), "provider": "vlm"}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"]["code"], "provider_unconfigured")

    def test_real_fts_changes_with_user_added_events_and_chat_persists(self):
        initial = self.client.get("/api/events/search", query_string={"q": "paystack"}).get_json()
        self.assertEqual(initial["backend"], "sqlite-fts5")
        self.assertEqual(initial["total"], 0)
        created = self.client.post("/api/events", json={"service": "paystack", "level": "warning", "message": "Payment queue delay for customer batch"})
        self.assertEqual(created.status_code, 201)
        changed = self.client.get("/api/events/search", query_string={"q": "paystack"}).get_json()
        self.assertEqual(changed["total"], 1)
        self.assertEqual(changed["hits"][0]["service"], "paystack")
        room = self.client.post("/api/chat/rooms", json={"title": "Payments"}).get_json()["room"]
        result = self.client.post(f"/api/chat/rooms/{room['id']}/messages", json={"message": "paystack", "mode": "search"})
        self.assertEqual(result.status_code, 201)
        payload = result.get_json()
        self.assertEqual(payload["message"]["metadata"]["kind"], "search-results")
        self.assertEqual(payload["message"]["metadata"]["hits"][0]["service"], "paystack")
        self.assertEqual(len(payload["toolcalls"]), 1)
        restarted = create_app({"data_dir": self.temp.name, "model_base_url": "", "model_name": "", "es_url": ""})
        client = restarted.test_client()
        saved = client.get(f"/api/chat/rooms/{room['id']}").get_json()["room"]
        self.assertEqual(len(saved["messages"]), 2)
        self.assertEqual(saved["messages"][1]["metadata"]["hits"][0]["service"], "paystack")
        self.assertEqual(len(saved["toolcalls"]), 1)
        self.assertIn("assistant", client.get(f"/api/chat/rooms/{room['id']}/export").get_data(as_text=True))

    def test_mcp_rejects_missing_unknown_skill_and_forbidden_tool_before_dispatch(self):
        missing = self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        wrong = self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "context": {"active_skill": "admin"}})
        forbidden = self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 3, "method": "tools/call", "context": {"active_skill": "elasticsearch-ops"}, "params": {"name": "delete_index", "arguments": {"index": "public-ops-events"}}})
        self.assertEqual(missing.status_code, 403)
        self.assertEqual(wrong.status_code, 403)
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.get_json()["error"]["code"], -32003)
        allowed = self.client.post("/mcp", json={"jsonrpc": "2.0", "id": 4, "method": "tools/call", "context": {"active_skill": "elasticsearch-ops"}, "params": {"name": "es_search", "arguments": {"index": "public-ops-events", "query": "saturation"}}})
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.get_json()["result"]["structuredContent"]["total"], 1)

    def test_mcp_rejects_malformed_jsonrpc_params_and_arguments_with_jsonrpc_errors(self):
        context = {"active_skill": "elasticsearch-ops"}
        malformed = [
            {"jsonrpc": "1.0", "id": 1, "method": "tools/list", "context": context},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": [], "context": context},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": ["es_search"]}, "context": context},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "es_search", "arguments": []}, "context": context},
        ]
        responses = [self.client.post("/mcp", json=item) for item in malformed]
        self.assertEqual([response.status_code for response in responses], [400, 400, 403, 400])
        self.assertEqual(responses[1].get_json()["error"]["code"], -32602)
        self.assertEqual(responses[2].get_json()["error"]["code"], -32003)
        self.assertEqual(responses[3].get_json()["error"]["code"], -32602)

    def test_elasticsearch_write_failure_returns_single_json_error_tuple(self):
        app = create_app({"data_dir": self.temp.name, "es_url": "http://127.0.0.1:1"})
        response = app.test_client().post("/api/events", json={"service": "synthetic", "level": "warning", "message": "synthetic outage"})
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["error"]["code"], "elasticsearch_unavailable")

    def test_configured_model_http_request_executes_only_authorized_search_tool(self):
        seen = []
        state = {"calls": 0}
        token = "model-test-token"

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                seen.append({"path": self.path, "authorization": self.headers.get("Authorization"), "payload": payload})
                state["calls"] += 1
                if state["calls"] == 1:
                    message = {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1", "type": "function", "function": {"name": "es_search", "arguments": json.dumps({"index": "public-ops-events", "query": "connection pool"})}}]}
                else:
                    message = {"role": "assistant", "content": "The ledger database reported connection pool saturation."}
                data = json.dumps({"choices": [{"message": message}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            app = create_app({"data_dir": self.temp.name, "model_base_url": f"http://127.0.0.1:{server.server_port}/v1", "model_name": "local-model", "model_api_key": token, "litellm_management_api_key": "management-only-secret"})
            client = app.test_client()
            room = client.post("/api/chat/rooms", json={}).get_json()["room"]
            response = client.post(f"/api/chat/rooms/{room['id']}/messages", json={"message": "What happened to the ledger database?", "mode": "llm"})
            self.assertEqual(response.status_code, 201, response.get_json())
            result = response.get_json()
            self.assertIn("connection pool saturation", result["message"]["content"])
            self.assertEqual(len(result["toolcalls"]), 1)
            self.assertEqual(state["calls"], 2)
            self.assertTrue(all(item["path"] == "/v1/chat/completions" for item in seen))
            self.assertTrue(all(item["authorization"] == f"Bearer {token}" for item in seen))
            self.assertTrue(all(item["authorization"] != "Bearer management-only-secret" for item in seen))
            self.assertEqual(seen[0]["payload"]["model"], "local-model")
            self.assertNotIn(token, json.dumps(result))
            persisted = client.get(f"/api/chat/rooms/{room['id']}").get_json()["room"]
            self.assertEqual(len(persisted["toolcalls"]), 1)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
