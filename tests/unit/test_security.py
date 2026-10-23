from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.exceptions import InvalidTag

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_pdf_payload,
    encrypt_pdf_payload,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery-staple")
    assert hashed != "correct-horse-battery-staple"
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_same_password_hashes_differently():
    assert hash_password("same-password-1") != hash_password("same-password-1")


def test_pdf_encryption_roundtrip_and_unique_nonce():
    payload = b"%PDF-1.4 fake pdf bytes"
    a, b = encrypt_pdf_payload(payload), encrypt_pdf_payload(payload)
    assert a != payload and a != b
    assert decrypt_pdf_payload(a) == payload


def test_tampered_ciphertext_is_rejected():
    blob = bytearray(encrypt_pdf_payload(b"secret resume"))
    blob[-1] ^= 1
    with pytest.raises(InvalidTag):
        decrypt_pdf_payload(bytes(blob))


def test_truncated_payload_is_rejected():
    with pytest.raises(ValueError):
        decrypt_pdf_payload(b"short")


def test_token_types_and_subject():
    assert decode_token(create_access_token(7))["type"] == "access"
    refresh = decode_token(create_refresh_token(7))
    assert refresh["type"] == "refresh" and refresh["sub"] == "7"


def test_expired_token_is_rejected():
    expired = jwt.encode(
        {"sub": "1", "type": "access", "exp": datetime.now(timezone.utc) - timedelta(seconds=5)},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_token(expired)
