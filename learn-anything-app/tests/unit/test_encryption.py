import os
import tempfile
from app.security.encryption import SecretStore


def test_encrypt_decrypt_roundtrip():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    try:
        store = SecretStore(key_path)
        plaintext = "sk-ant-api03-very-secret-key"
        encrypted = store.encrypt(plaintext)
        assert encrypted != plaintext
        assert store.decrypt(encrypted) == plaintext
    finally:
        os.unlink(key_path)


def test_key_auto_generated():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    os.unlink(key_path)  # Delete so it auto-generates
    try:
        store = SecretStore(key_path)
        assert os.path.exists(key_path)
        assert store.encrypt("test") != "test"
    finally:
        os.unlink(key_path)


def test_different_encryptions_differ():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as f:
        key_path = f.name
    try:
        store = SecretStore(key_path)
        e1 = store.encrypt("same")
        e2 = store.encrypt("same")
        assert e1 != e2  # Different nonces
    finally:
        os.unlink(key_path)
