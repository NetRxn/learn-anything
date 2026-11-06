# app/security/encryption.py
import base64
import os
import tempfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretStore:
    def __init__(self, key_path: str):
        self._key_path = Path(key_path)
        self._key = self._load_or_generate_key()

    def _load_or_generate_key(self) -> bytes:
        self._key_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if not self._key_path.exists():
            key = AESGCM.generate_key(bit_length=256)
            fd, temporary = tempfile.mkstemp(dir=self._key_path.parent)
            try:
                with os.fdopen(fd, "wb") as stream:
                    stream.write(key)
                    stream.flush()
                    os.fsync(stream.fileno())
                try:
                    # Publish a complete key without replacing a concurrent winner.
                    os.link(temporary, self._key_path)
                except FileExistsError:
                    pass
            finally:
                os.unlink(temporary)
        key = self._key_path.read_bytes()
        if len(key) != 32:
            raise ValueError("Encryption key must contain exactly 32 bytes")
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
