def test_password_hash_accepts_long_password() -> None:
    from src.apps.users.auth import hash_password, verify_password

    long_pw = "x" * 200
    hashed = hash_password(long_pw)
    assert verify_password(long_pw, hashed)


def test_password_verify_legacy_raw_bcrypt() -> None:
    """Hashes created with bcrypt(raw password) before SHA-256 pre-hashing."""
    import bcrypt

    from src.apps.users.auth import verify_password

    raw = b"password12"
    hashed = bcrypt.hashpw(raw, bcrypt.gensalt()).decode("ascii")
    assert verify_password("password12", hashed)
