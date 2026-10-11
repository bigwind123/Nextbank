"""Risk-focused tests for duplicate writes, privacy boundaries, and MCP dispatch."""
import unittest
from cryptography.exceptions import InvalidTag

from examples.gateway import FakeNativeProvider, PublicationGateway
from examples.ocr import EncryptedTokenMap, Profile, SafePreparationError, prepare_outbound
from examples.mcp import DispatchDenied, MockProvider, SKILL_CONFIG, SkillScopedMCP


class GatewayRecoveryTests(unittest.TestCase):
    def test_timeout_after_apply_recovers_by_provenance_without_recreation(self):
        provider = FakeNativeProvider(timeout_after_apply=True)
        gateway = PublicationGateway(provider)
        payload = {"name": "fictional"}
        self.assertEqual("unknown", gateway.publish("req-1", payload)["state"])
        self.assertEqual("published", gateway.publish("req-1", payload)["state"])
        self.assertEqual("conflict", gateway.publish("req-1", {"name": "changed"})["state"])
        self.assertEqual("conflict", gateway.publish("req-1", payload, actor="other-operator")["state"])
        self.assertEqual("published", gateway.publish("req-1", payload)["state"])
        self.assertEqual(1, provider.apply_count)

    def test_readback_failure_stays_unknown_without_recreation(self):
        provider = FakeNativeProvider(timeout_after_apply=True, readback_failure=True)
        gateway = PublicationGateway(provider)
        self.assertEqual("unknown", gateway.publish("req-2", {"name": "fictional"})["state"])
        self.assertEqual("unknown", gateway.publish("req-2", {"name": "fictional"})["state"])
        self.assertEqual(1, provider.apply_count)

    def test_native_identity_and_ownership_metadata_must_match(self):
        for field in ("provider_id", "operation_id", "actor", "payload"):
            with self.subTest(field=field):
                provider = FakeNativeProvider(timeout_after_apply=True, readback_corruption=field)
                gateway = PublicationGateway(provider)
                payload = {"name": "fictional"}
                self.assertEqual("unknown", gateway.publish("req-3", payload)["state"])
                self.assertEqual("unknown", gateway.confirm("req-3")["state"])
                self.assertEqual(1, provider.apply_count)

    def test_mismatched_readback_never_confirms_or_recreates(self):
        provider = FakeNativeProvider(timeout_after_apply=True, readback_mismatch=True)
        gateway = PublicationGateway(provider)
        payload = {"name": "fictional"}
        self.assertEqual("unknown", gateway.publish("req-1", payload)["state"])
        self.assertEqual("unknown", gateway.publish("req-1", payload)["state"])
        self.assertEqual(1, provider.apply_count)


class OCRBoundaryTests(unittest.TestCase):
    def test_only_profile_fields_leave_and_protected_values_are_stable_and_reversible(self):
        mapping = EncryptedTokenMap("doc-1", secret=b"x" * 32)
        profile = Profile(frozenset({"name", "income", "account"}), frozenset({"name", "account"}))
        raw = {"name": "Fictional Person", "income": 3, "account": "0000", "unexpected": "leak"}
        outbound = prepare_outbound(profile, raw, mapping=mapping)
        self.assertEqual({"name", "income", "account", "provenance"}, set(outbound))
        self.assertEqual({"document_id": "fictional-document-001", "page_number": 1}, outbound["provenance"])
        self.assertNotIn("Fictional Person", repr(outbound))
        self.assertEqual(outbound["name"], mapping.tokenize("Fictional Person"))
        with self.assertRaises(PermissionError):
            mapping.reveal(outbound["name"])
        self.assertEqual("Fictional Person", mapping.reveal(outbound["name"], authorized=True))
        self.assertEqual("token_reversal", mapping.audit_log[0]["event"])
        another_document = EncryptedTokenMap("doc-2", secret=b"x" * 32)
        self.assertNotEqual(outbound["name"], another_document.tokenize("Fictional Person"))
        self.assertGreaterEqual(len(outbound["name"].removeprefix("PERSON_")), 32)

    def test_ciphertext_tampering_fails_authentication(self):
        mapping = EncryptedTokenMap("doc-1", secret=b"x" * 32)
        token = mapping.tokenize("Fictional")
        nonce, ciphertext = mapping._ciphertext[token]
        mapping._ciphertext[token] = (nonce, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]))
        with self.assertRaises(InvalidTag):
            mapping.reveal(token, authorized=True)

    def test_missing_profile_or_unmapped_protected_field_fails_closed(self):
        mapping = EncryptedTokenMap("doc-1", secret=b"x" * 32)
        with self.assertRaises(SafePreparationError):
            prepare_outbound(None, {"name": "Fictional"}, mapping=mapping)
        profile = Profile(frozenset({"name"}), frozenset({"name"}))
        with self.assertRaises(SafePreparationError):
            prepare_outbound(profile, {"name": None}, mapping=mapping)

    def test_protected_field_must_be_allowlisted_and_group_pii_is_rejected(self):
        mapping = EncryptedTokenMap("doc-1", secret=b"x" * 32)
        bad = Profile(frozenset({"income"}), frozenset({"name"}))
        with self.assertRaises(SafePreparationError):
            prepare_outbound(bad, {"name": "Fictional"}, mapping=mapping)
        grouped = Profile(frozenset({"rows"}), frozenset(), frozenset({"rows"}))
        with self.assertRaises(SafePreparationError):
            prepare_outbound(grouped, {"rows": []}, mapping=mapping)

    def test_nested_values_and_invalid_provenance_fail_before_payload_is_built(self):
        mapping = EncryptedTokenMap("doc-1", secret=b"x" * 32)
        profile = Profile(frozenset({"income", "note"}), frozenset())
        for values, kwargs in (
            ({"income": {"nested": "value"}}, {}),
            ({"income": [1, 2]}, {}),
            ({"income": float("nan")}, {}),
            ({"income": 10}, {"document_id": {"nested": "document"}}),
            ({"income": 10}, {"document_id": "  "}),
            ({"income": 10}, {"page_number": {"nested": 1}}),
            ({"income": 10}, {"page_number": True}),
            ({"income": 10}, {"page_number": 0}),
        ):
            with self.subTest(values=values, kwargs=kwargs):
                with self.assertRaises(SafePreparationError):
                    prepare_outbound(profile, values, mapping=mapping, **kwargs)
                self.assertEqual({}, mapping._ciphertext)


class MCPDispatchTests(unittest.TestCase):
    def test_unconfigured_and_forbidden_tools_never_reach_provider(self):
        provider = MockProvider()
        server = SkillScopedMCP(provider, None)
        self.assertEqual([], server.tool_list("es-dev-apm"))
        none_config = SkillScopedMCP(provider, {"es-dev-apm": None})
        self.assertEqual([], none_config.tool_list("es-dev-apm"))
        request = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                   "params": {"name": "es_search", "arguments": {}}}
        with self.assertRaises(DispatchDenied):
            server.dispatch("es-dev-apm", request)
        configured = SkillScopedMCP(provider, SKILL_CONFIG)
        request["params"]["name"] = "mssql_execute"
        with self.assertRaises(DispatchDenied):
            configured.dispatch("es-dev-apm", request)
        self.assertEqual([], provider.calls)

    def test_allowed_tool_returns_offline_json_rpc_shape(self):
        provider = MockProvider()
        server = SkillScopedMCP(provider, SKILL_CONFIG)
        request = {"jsonrpc": "2.0", "id": "q1", "method": "tools/call",
                   "params": {"name": "es_esql", "arguments": {"query": "SHOW INFO"}}}
        response = server.dispatch("es-dev-apm", request)
        self.assertEqual(("esql", {"query": "SHOW INFO"}), provider.calls[0])
        self.assertEqual("q1", response["id"])
        self.assertEqual("2.0", response["jsonrpc"])


if __name__ == "__main__":
    unittest.main()
