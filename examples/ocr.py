"""Offline, profile-scoped OCR payload preparation with encrypted token mapping."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
import math
import secrets
from typing import Any, Protocol

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:  # Fail closed; never substitute home-grown encryption.
    AESGCM = None  # type: ignore[assignment,misc]


class SafePreparationError(ValueError):
    pass


class Extractor(Protocol):
    def extract(self, document: bytes) -> dict[str, Any]: ...


class FictionalOfflineExtractor:
    """Deterministic stand-in for an OCR/VLM endpoint; it performs no inference."""

    def extract(self, document: bytes) -> dict[str, Any]:
        if not document.startswith(b"FICTIONAL-DEMO:"):
            raise SafePreparationError("fixture accepts fictional demo input only")
        return {"applicant_name": "Fictional Person", "monthly_income": 84000,
                "account_number": "0000-1234-5678", "notes": "not in profile"}


@dataclass(frozen=True)
class Profile:
    allowed_fields: frozenset[str]
    protected_fields: frozenset[str]
    group_fields: frozenset[str] = frozenset()


class EncryptedTokenMap:
    """Document-scoped stable pseudonyms; key and encrypted map live in memory."""

    def __init__(self, document_scope: str, secret: bytes | None = None):
        if AESGCM is None:
            raise SafePreparationError("cryptography is required for AES-GCM token mapping")
        self._secret = secret or secrets.token_bytes(32)
        self._document_scope = document_scope
        self._ciphertext: dict[str, tuple[bytes, bytes]] = {}
        self.audit_log: list[dict[str, str]] = []

    def tokenize(self, value: str) -> str:
        raw = value.encode("utf-8")
        token = "PERSON_" + hmac.new(self._secret, self._document_scope.encode() + b"\0" + raw,
                                      hashlib.sha256).hexdigest()[:32].upper()
        if token not in self._ciphertext:
            nonce = secrets.token_bytes(12)
            encrypted = AESGCM(self._secret).encrypt(nonce, raw, self._document_scope.encode())
            self._ciphertext[token] = (nonce, encrypted)
        return token

    def reveal(self, token: str, *, authorized: bool = False) -> str:
        if not authorized:
            raise PermissionError("reversal requires explicit authorization")
        nonce, encrypted = self._ciphertext[token]
        value = AESGCM(self._secret).decrypt(nonce, encrypted, self._document_scope.encode()).decode()
        self.audit_log.append({"event": "token_reversal", "document_scope": self._document_scope,
                               "token": token})
        return value


def prepare_outbound(profile: Profile | None, model_fields: dict[str, Any], *,
                     mapping: EncryptedTokenMap, document_id: str = "fictional-document-001",
                     page_number: int = 1) -> dict[str, Any]:
    if profile is None:
        raise SafePreparationError("a configured profile is required")
    if profile.group_fields:
        raise SafePreparationError("group-valued fields with PII are not supported by this example")
    if not profile.protected_fields <= profile.allowed_fields:
        raise SafePreparationError("protected fields must be explicitly allowlisted")
    if not isinstance(document_id, str) or not document_id.strip():
        raise SafePreparationError("document_id must be a non-empty string")
    if type(page_number) is not int or page_number < 1:
        raise SafePreparationError("page_number must be a positive integer")
    # Unknown source fields are dropped; only the profile's allowlist is outbound.
    outbound = {name: value for name, value in model_fields.items() if name in profile.allowed_fields}
    for name, value in outbound.items():
        scalar = (value is None or type(value) in (str, int, bool)
                  or (type(value) is float and math.isfinite(value)))
        if not scalar:
            raise SafePreparationError(f"field {name!r} must be a JSON scalar in this flat example")
    for name in profile.protected_fields:
        if name not in model_fields:
            continue
        value = model_fields[name]
        if not isinstance(value, str) or not value:
            raise SafePreparationError(f"protected field {name!r} has no safe mapping")
        outbound[name] = mapping.tokenize(value)
    outbound["provenance"] = {"document_id": document_id, "page_number": page_number}
    return outbound


class FictionalOfflineStageTwo:
    """Return a fixed, fictional validation result without inference or formulas."""

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        if "provenance" not in payload:
            raise SafePreparationError("stage-two payload requires document provenance")
        return {"result": "fictional_manual_review", "provenance": payload["provenance"]}


def demo() -> str:
    # Stage 1: extraction happens before any replacement. Profile is fictional and explicit.
    model_output = FictionalOfflineExtractor().extract(b"FICTIONAL-DEMO: sample statement")
    profile = Profile(allowed_fields=frozenset({"applicant_name", "monthly_income", "account_number"}),
                      protected_fields=frozenset({"applicant_name", "account_number"}))
    mapping = EncryptedTokenMap("fictional-document-001")
    outbound = prepare_outbound(profile, model_output, mapping=mapping)
    stage_two = FictionalOfflineStageTwo().validate(outbound)
    return json.dumps({"stage_1_model_fields": model_output, "stage_2_request_allowlist": outbound,
                       "stage_2_validated_demo_output": stage_two,
                       "example_only": True, "mapping_secret_printed": False}, indent=2)


if __name__ == "__main__":
    print(demo())
