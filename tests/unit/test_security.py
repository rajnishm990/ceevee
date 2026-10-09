from app.core.security import decrypt_pdf_payload, encrypt_pdf_payload, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_pdf_encryption_roundtrip():
    payload = b"%PDF-1.4 fake pdf bytes for testing"
    encrypted = encrypt_pdf_payload(payload)
    assert encrypted != payload
    assert decrypt_pdf_payload(encrypted) == payload
