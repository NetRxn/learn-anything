# app/security/encryption.py
import base64
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretStore:
    def __init__(self, key_path: str):
        self._key_path = Path(key_path)
        self._key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> bytes:
        if self._key_path.exists() and self._key_path.stat().st_size > 0:
            return self._key_path.read_bytes()
        key = AESGCM.generate_key(bit_length=256)
        self._key_path.parent.mkdir(parents=True, exist_ok=True)
        self._key_path.write_bytes(key)
        self._key_path.chmod(0o600)
        return key

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        aesgcm = AESGCM(self._key)
        ct = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ct).decode()

    def decrypt(self, token: str) -> str:
        raw = base64.b64decode(token)
        nonce, ct = raw[:12], raw[12:]
        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, ct, None).decode()
