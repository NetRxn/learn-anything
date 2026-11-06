from app.security.passwords import hash_password, verify_password


def test_hash_and_verify():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_hash_is_unique():
    h1 = hash_password("same-password")
    h2 = hash_password("same-password")
    assert h1 != h2  # Different salts
