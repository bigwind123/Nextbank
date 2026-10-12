from __future__ import annotations

import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from public_app import create_app
from public_app.providers import LiteLLMProvider, OperationProvenance, ProviderError, WriteUncertain


class RuntimeGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({"data_dir": self.temp.name, "model_base_url": "", "litellm_url": ""})
        self.app.testing = True
        self.client = self.app.test_client()
        self.workspace = self.client.post("/api/workspaces", json={"name": "Synthetic Workspace"}).get_json()["workspace"]
        self.model = self.client.post("/api/models", json={"name": "synthetic-chat"}).get_json()["model"]

    def tearDown(self):
        self.temp.cleanup()

    def approve(self):
        return self.client.post(f"/api/workspaces/{self.workspace['id']}/approve", json={"model_id": self.model["id"]})

    def select(self, key="request-001", **kwargs):
        return self.client.post(
            f"/api/workspaces/{self.workspace['id']}/select",
            json={"model_id": self.model["id"], "idempotency_key": key, **kwargs},
        )

    def receipt_count(self):
        db = self.app.extensions["portfolio_database"]
        with db.connect() as connection:
            return connection.execute("SELECT COUNT(*) FROM registry_selection_receipts").fetchone()[0]

    def test_approval_is_required_before_selection(self):
        response = self.select()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "approval_required")
        self.assertEqual(self.receipt_count(), 0)

    def test_timeout_after_apply_is_unknown_then_provenance_readback_confirms(self):
        self.approve()
        first = self.select(simulate_timeout=True)
        self.assertEqual(first.status_code, 202)
        operation = first.get_json()["operation"]
        self.assertEqual(operation["state"], "unknown")
        self.assertEqual(self.receipt_count(), 1)

        recovered = self.client.post(f"/api/operations/{operation['id']}/reconcile").get_json()
        self.assertTrue(recovered["confirmed"])
        self.assertEqual(recovered["operation"]["state"], "selected")
        self.assertEqual(self.receipt_count(), 1)

    def test_same_idempotency_replay_does_not_apply_twice_and_conflict_rejects(self):
        self.approve()
        another_model = self.client.post("/api/models", json={"name": "second-model"}).get_json()["model"]
        self.client.post(f"/api/workspaces/{self.workspace['id']}/approve", json={"model_id": another_model["id"]})
        first = self.select()
        self.assertEqual(first.status_code, 200)
        first_op = first.get_json()["operation"]
        replay = self.select()
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.get_json()["operation"]["id"], first_op["id"])
        self.assertEqual(self.receipt_count(), 1)

        conflict = self.select(actor_id="different-local-actor")
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.get_json()["error"]["code"], "idempotency_conflict")
        changed_payload = self.client.post(
            f"/api/workspaces/{self.workspace['id']}/select",
            json={"model_id": another_model["id"], "idempotency_key": "request-001", "actor_id": "local-user"},
        )
        self.assertEqual(changed_payload.status_code, 409)
        self.assertEqual(self.receipt_count(), 1)

    def test_mismatched_readback_stays_unknown_and_does_not_recreate(self):
        self.approve()
        first = self.select(simulate_timeout=True)
        operation_id = first.get_json()["operation"]["id"]
        db = self.app.extensions["portfolio_database"]
        with db.connect() as connection:
            connection.execute("UPDATE registry_selection_receipts SET actor_id='wrong-actor' WHERE operation_id=?", (operation_id,))
        result = self.client.post(f"/api/operations/{operation_id}/reconcile").get_json()
        self.assertFalse(result["confirmed"])
        self.assertEqual(result["operation"]["state"], "unknown")
        self.assertEqual(self.receipt_count(), 1)

    def test_new_idempotency_key_is_blocked_while_matching_operation_is_unresolved(self):
        self.approve()
        first = self.select(key="first-key", simulate_timeout=True)
        self.assertEqual(first.status_code, 202)
        blocked = self.select(key="second-key")
        self.assertEqual(blocked.status_code, 409)
        self.assertEqual(blocked.get_json()["error"]["code"], "operation_unresolved")
        self.assertEqual(blocked.get_json()["operation"]["id"], first.get_json()["operation"]["id"])
        self.assertEqual(self.receipt_count(), 1)
        reconciled = self.client.post(f"/api/operations/{first.get_json()['operation']['id']}/reconcile")
        self.assertEqual(reconciled.get_json()["operation"]["state"], "selected")
        allowed = self.select(key="second-key")
        self.assertEqual(allowed.status_code, 200)

    def test_local_catalog_and_operations_survive_app_restart(self):
        self.approve()
        first = self.select()
        operation_id = first.get_json()["operation"]["id"]
        restarted = create_app({"data_dir": self.temp.name, "model_base_url": "", "litellm_url": ""})
        client = restarted.test_client()
        self.assertEqual(len(client.get("/api/workspaces").get_json()["workspaces"]), 2)
        self.assertEqual(len(client.get("/api/models").get_json()["models"]), 2)
        self.assertEqual(client.get("/api/operations").get_json()["operations"][0]["id"], operation_id)

    def test_settings_only_accept_public_values_and_reject_embedded_url_credentials(self):
        initial_health = self.client.get("/api/health").get_json()
        self.assertEqual(initial_health["chat_mode"], "search-only")
        self.assertEqual(initial_health["mcp_mode"], "sqlite-fts5")
        leaked = self.client.post("/api/settings", json={"litellm_api_key": "should-not-be-accepted"})
        self.assertEqual(leaked.status_code, 400)
        embedded = self.client.post("/api/settings", json={"litellm_url": "https://user:pass@example.invalid"})
        self.assertEqual(embedded.status_code, 400)
        updated = self.client.post("/api/settings", json={"model_base_url": "http://127.0.0.1:9900/v1", "model_name": "local-model"})
        self.assertEqual(updated.status_code, 200)
        self.client.post("/api/settings", json={"es_url": "http://127.0.0.1:9200"})
        refreshed_health = self.client.get("/api/health").get_json()
        self.assertEqual(refreshed_health["chat_mode"], "configured-model")
        self.assertEqual(refreshed_health["mcp_mode"], "elasticsearch")
        settings = self.client.get("/api/settings").get_json()
        self.assertNotIn("litellm_management_api_key", settings["settings"])
        restarted = create_app({"data_dir": self.temp.name, "model_base_url": "", "litellm_url": ""})
        persisted = restarted.test_client().get("/api/settings").get_json()["settings"]
        self.assertEqual(persisted["model_base_url"], "http://127.0.0.1:9900/v1")
        self.assertEqual(persisted["model_name"], "local-model")

    def test_unchanged_management_url_can_be_saved_with_other_settings_but_changes_are_locked(self):
        with tempfile.TemporaryDirectory() as temp:
            app = create_app({
                "data_dir": temp,
                "litellm_url": "http://127.0.0.1:4000",
                "litellm_management_api_key": "management-secret",
            })
            client = app.test_client()
            accepted = client.post("/api/settings", json={
                "litellm_url": "http://127.0.0.1:4000",
                "model_name": "review-model",
            })
            self.assertEqual(accepted.status_code, 200, accepted.get_json())
            changed = client.post("/api/settings", json={
                "litellm_url": "http://127.0.0.1:4001",
                "model_name": "must-not-save",
            })
            self.assertEqual(changed.status_code, 409)
            settings = client.get("/api/settings").get_json()["settings"]
            self.assertEqual(settings["litellm_url"], "http://127.0.0.1:4000")
            self.assertEqual(settings["model_name"], "review-model")

    def test_workspace_and_model_crud_blocks_deleting_referenced_records(self):
        renamed = self.client.patch(f"/api/workspaces/{self.workspace['id']}", json={"name": "Renamed Workspace"})
        self.assertEqual(renamed.status_code, 200)
        self.assertEqual(renamed.get_json()["workspace"]["name"], "Renamed Workspace")
        model_update = self.client.patch(f"/api/models/{self.model['id']}", json={"name": "renamed-model"})
        self.assertEqual(model_update.status_code, 200)
        self.assertEqual(model_update.get_json()["model"]["name"], "renamed-model")
        self.assertEqual(self.client.delete(f"/api/workspaces/{self.workspace['id']}").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/models/{self.model['id']}").status_code, 204)

        protected_workspace = self.client.post("/api/workspaces", json={"name": "Protected Workspace"}).get_json()["workspace"]
        protected_model = self.client.post("/api/models", json={"name": "protected-model"}).get_json()["model"]
        self.client.post(f"/api/workspaces/{protected_workspace['id']}/approve", json={"model_id": protected_model["id"]})
        self.client.post(f"/api/workspaces/{protected_workspace['id']}/select", json={"model_id": protected_model["id"], "idempotency_key": "keep-record"})
        self.assertEqual(self.client.delete(f"/api/workspaces/{protected_workspace['id']}").status_code, 409)
        self.assertEqual(self.client.delete(f"/api/models/{protected_model['id']}").status_code, 409)


class LocalRequestBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = create_app({"data_dir": self.temp.name})
        self.app.testing = True
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def workspace_count(self):
        db = self.app.extensions["portfolio_database"]
        with db.connect() as connection:
            return connection.execute("SELECT COUNT(*) FROM workspaces").fetchone()[0]

    def test_non_loopback_host_and_cross_origin_cannot_mutate_before_handler(self):
        before = self.workspace_count()
        bad_host = self.client.post("/api/workspaces", json={"name": "must not exist"}, headers={"Host": "attacker.invalid"})
        self.assertEqual(bad_host.status_code, 403)
        self.assertEqual(bad_host.get_json()["error"]["code"], "invalid_host")
        self.assertEqual(self.workspace_count(), before)

        bad_origin = self.client.post("/api/workspaces", json={"name": "must not exist"}, headers={"Origin": "https://attacker.invalid"})
        self.assertEqual(bad_origin.status_code, 403)
        self.assertEqual(bad_origin.get_json()["error"]["code"], "origin_forbidden")
        self.assertEqual(self.workspace_count(), before)

    def test_no_origin_local_client_and_exact_same_origin_are_allowed(self):
        no_origin = self.client.post("/api/workspaces", json={"name": "local client"})
        self.assertEqual(no_origin.status_code, 201)
        same_origin = self.client.post(
            "/api/workspaces", json={"name": "browser client"},
            base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"},
        )
        self.assertEqual(same_origin.status_code, 201)

    def test_mcp_route_is_blocked_by_central_host_origin_guard(self):
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "context": {"active_skill": "elasticsearch-ops"}}
        response = self.client.post("/mcp", json=payload, headers={"Origin": "http://untrusted.invalid"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()["error"]["code"], "origin_forbidden")


class PublicStaticRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.client = create_app({"data_dir": self.temp.name}).test_client()

    def tearDown(self):
        self.temp.cleanup()

    def test_tracked_portfolio_links_are_served_from_allowlisted_public_paths(self):
        paths = (
            "/portfolio",
            "/README.md",
            "/demo.en.html",
            "/assets/portfolio.css",
            "/assets/diagrams/platform-overview.html",
            "/assets/diagrams/platform-overview.svg",
            "/assets/screenshots/platform-overview.en.png",
            "/docs/public-runtime.md",
            "/case-studies/model-gateway.md",
            "/examples/README.md",
            "/examples/SCENARIOS.md",
            "/third_party/ARCHIFY_LICENSE",
        )
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertGreater(len(response.data), 0)
                response.close()

    def test_static_routes_do_not_expose_private_or_unlisted_source_paths(self):
        paths = (
            "/.local/runtime-config.json",
            "/.git/config",
            "/public_app/config.py",
            "/public_app/ocr.py",
            "/tools/build_diagrams.mjs",
            "/examples/gateway.py",
            "/assets/unknown.txt",
            "/docs/unknown.py",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)


class LiteLLMAdapterTests(unittest.TestCase):
    def test_nested_team_info_with_null_metadata_is_normalized_before_update_and_reconciled(self):
        state = {"metadata": None, "models": []}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def send_json(self, value):
                body = json.dumps(value).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self.send_json({"team_info": {"team_id": "team-null", "models": state["models"], "metadata": state["metadata"]}, "keys": []})

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                state["models"], state["metadata"] = payload["models"], payload["metadata"]
                self.send_json({"team_info": {"team_id": "team-null", "models": state["models"], "metadata": state["metadata"]}})

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            provider = LiteLLMProvider(f"http://127.0.0.1:{server.server_port}", "test-key")
            operation = OperationProvenance("op-null", "actor", "fingerprint", "workspace", "model", "sample-model")
            provider.apply_selection(operation, native_team_id="team-null")
            self.assertEqual(state["metadata"]["portfolio_operations"]["op-null"]["actor_id"], "actor")
            self.assertEqual(provider.readback(operation, native_team_id="team-null")["operation_id"], "op-null")

            state["metadata"] = []
            with self.assertRaises(ProviderError):
                provider.apply_selection(operation, native_team_id="team-null")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_management_authorization_does_not_follow_cross_authority_redirect(self):
        second_server_calls = []

        class RedirectHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{second.server_port}/stolen")
                self.end_headers()

        class CaptureHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                second_server_calls.append(self.headers.get("Authorization"))
                self.send_response(200)
                self.end_headers()

        second = ThreadingHTTPServer(("127.0.0.1", 0), CaptureHandler)
        first = ThreadingHTTPServer(("127.0.0.1", 0), RedirectHandler)
        servers = (first, second)
        threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in servers]
        for thread in threads:
            thread.start()
        try:
            provider = LiteLLMProvider(f"http://127.0.0.1:{first.server_port}", "management-secret")
            with self.assertRaises(WriteUncertain):
                provider._request("GET", "/team/info")
            self.assertEqual(second_server_calls, [])
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(timeout=2)

    def test_management_http_adapter_writes_then_reconciles_metadata_without_exposing_key(self):
        state = {"models": [], "metadata": {"keep": "existing"}, "authorization": []}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def send_json(self, value):
                body = json.dumps(value).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                state["authorization"].append(self.headers.get("Authorization"))
                self.send_json({"team_info": {"team_id": "team-fixture", "models": state["models"], "metadata": state["metadata"]}, "keys": []})

            def do_POST(self):
                state["authorization"].append(self.headers.get("Authorization"))
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                state["models"] = payload["models"]
                state["metadata"] = payload["metadata"]
                self.send_json({"team_info": {"team_id": payload["team_id"], "models": state["models"], "metadata": state["metadata"]}})

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        temp = tempfile.TemporaryDirectory()
        try:
            base_url = f"http://127.0.0.1:{server.server_port}"
            app = create_app({
                "data_dir": temp.name,
                "litellm_url": base_url,
                "litellm_management_api_key": "test-secret-never-returned",
            })
            client = app.test_client()
            workspace = client.post("/api/workspaces", json={
                "name": "Remote Team Mapping", "native_team_id": "team-fixture",
            }).get_json()["workspace"]
            model = client.post("/api/models", json={"name": "safe-model"}).get_json()["model"]
            client.post(f"/api/workspaces/{workspace['id']}/approve", json={"model_id": model["id"]})
            result = client.post(f"/api/workspaces/{workspace['id']}/select", json={
                "model_id": model["id"], "idempotency_key": "remote-test", "simulate_timeout": True,
            })
            self.assertEqual(result.status_code, 202)
            self.assertEqual(result.get_json()["operation"]["state"], "unknown")
            operation_id = result.get_json()["operation"]["id"]
            confirmed = client.post(f"/api/operations/{operation_id}/reconcile").get_json()
            self.assertTrue(confirmed["confirmed"])
            self.assertEqual(confirmed["operation"]["state"], "selected")
            self.assertEqual(state["models"], ["safe-model"])
            self.assertEqual(state["metadata"]["keep"], "existing")
            self.assertTrue(all(value == "Bearer test-secret-never-returned" for value in state["authorization"]))
            settings_text = json.dumps(client.get("/api/settings").get_json())
            response_text = json.dumps(result.get_json()) + json.dumps(confirmed)
            self.assertNotIn("test-secret-never-returned", settings_text + response_text)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            temp.cleanup()


if __name__ == "__main__":
    unittest.main()
