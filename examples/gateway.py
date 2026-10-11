"""Offline model of idempotent native publication and timeout recovery."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


class TimeoutAfterApply(TimeoutError):
    """The provider applied the write, but its response was lost."""


def fingerprint(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass
class Record:
    operation_id: str
    actor: str
    payload_fingerprint: str
    payload: dict[str, Any]
    state: str = "pending"
    provider_id: str | None = None


class FakeNativeProvider:
    """A tiny provider fixture; no HTTP client or network connection exists."""

    def __init__(self, *, timeout_after_apply: bool = False, readback_mismatch: bool = False,
                 readback_failure: bool = False, readback_corruption: str | None = None):
        self.objects: dict[str, dict[str, Any]] = {}
        self.timeout_after_apply = timeout_after_apply
        self.readback_mismatch = readback_mismatch
        self.readback_failure = readback_failure
        self.readback_corruption = readback_corruption
        self.apply_count = 0

    def create(self, operation_id: str, actor: str, payload: dict[str, Any], digest: str) -> str:
        self.apply_count += 1
        provider_id = f"native-{self.apply_count:03d}"
        self.objects[provider_id] = {
            "provider_id": provider_id,
            "operation_id": operation_id,
            "actor": actor,
            "fingerprint": digest,
            "payload": dict(payload),
        }
        if self.timeout_after_apply:
            self.timeout_after_apply = False
            raise TimeoutAfterApply("simulated response timeout after provider applied write")
        return provider_id

    def readback(self, provider_id: str) -> dict[str, Any] | None:
        if self.readback_failure:
            return None
        result = self.objects.get(provider_id)
        if result is None:
            return None
        result = dict(result)
        if self.readback_mismatch:
            result["fingerprint"] = "mismatch"
        if self.readback_corruption in result:
            result[self.readback_corruption] = "mismatch"
        return result

    def find_by_operation(self, operation_id: str) -> dict[str, Any] | None:
        """Explicit provenance lookup used when the create response lost its native ID."""
        matches = [value for value in self.objects.values() if value.get("operation_id") == operation_id]
        if len(matches) != 1 or self.readback_failure:
            return None
        result = dict(matches[0])
        if self.readback_mismatch:
            result["fingerprint"] = "mismatch"
        if self.readback_corruption in result:
            result[self.readback_corruption] = "mismatch"
        return result


class PublicationGateway:
    def __init__(self, provider: FakeNativeProvider):
        self.provider = provider
        self.operations: dict[str, Record] = {}

    def publish(self, idempotency_key: str, payload: dict[str, Any], *, actor: str = "demo-operator") -> dict[str, str]:
        digest = fingerprint(payload)
        record = self.operations.get(idempotency_key)
        if record:
            if record.payload_fingerprint != digest or record.actor != actor:
                return {"state": "conflict", "detail": "key was already used by another actor or for another payload"}
            if record.state == "published":
                return {"state": "published", "provider_id": record.provider_id or ""}
            if record.state == "unknown":
                # An unknown result is resolved only by explicit identity/provenance readback.
                return self.confirm(idempotency_key)
            return {"state": record.state, "detail": "operation is already recorded"}

        record = Record(idempotency_key, actor, digest, dict(payload))
        self.operations[idempotency_key] = record
        try:
            record.provider_id = self.provider.create(idempotency_key, actor, payload, digest)
        except TimeoutAfterApply:
            record.state = "unknown"
            return {"state": "unknown", "detail": "write may have applied; readback required"}
        record.state = "unknown"
        return self.confirm(idempotency_key)

    def confirm(self, idempotency_key: str) -> dict[str, str]:
        record = self.operations[idempotency_key]
        provider_id = record.provider_id
        if not provider_id:
            located = self.provider.find_by_operation(record.operation_id)
            provider_id = located.get("provider_id") if located else None
        # A provenance lookup only supplies a candidate ID. Confirmation still uses ID readback.
        actual = self.provider.readback(provider_id) if provider_id else None
        if not actual or actual.get("provider_id") != provider_id \
                or actual.get("operation_id") != idempotency_key \
                or actual.get("actor") != record.actor \
                or actual.get("payload") != record.payload \
                or actual.get("fingerprint") != record.payload_fingerprint:
            record.state = "unknown"
            return {"state": "unknown", "detail": "readback provenance or fingerprint mismatch"}
        record.provider_id = actual["provider_id"]
        record.state = "published"
        return {"state": "published", "provider_id": record.provider_id}


def demo() -> str:
    provider = FakeNativeProvider(timeout_after_apply=True)
    gateway = PublicationGateway(provider)
    payload = {"kind": "model", "name": "fictional-demo-model", "workspace": "demo-workspace"}
    first = gateway.publish("demo-request-001", payload)
    recovered = gateway.confirm("demo-request-001")
    replay = gateway.publish("demo-request-001", payload)
    return json.dumps({"first": first, "recovered": recovered, "replay": replay,
                       "provider_create_calls": provider.apply_count}, indent=2)


if __name__ == "__main__":
    print(demo())
