from __future__ import annotations

import base64

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def verify_ed25519(data: bytes, signature_base64: str, public_key_base64: str) -> bool:
    try:
        signature = base64.b64decode(signature_base64)
        public_key_bytes = base64.b64decode(public_key_base64)
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, data)
    except (InvalidSignature, ValueError):
        return False
    return True
