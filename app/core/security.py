import base64 
import os 
from datetime import datetime , timedelta , timezone 
from typing import Any , Dict , Tuple 
from argon2 import PasswordHasher 
from argon2.exceptions import VerifyMismatchError 
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import jwt 

from app.core.config import settings 

pwd_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,   #64 mb 
    parallelism=4,
    hash_len=32,
    salt_len=16
) 

_raw_enc_key = base64.b64decode(settings.PDF_ENCRYPTION_KEY)
aesgcm = AESGCM(_raw_enc_key)

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False 

def create_access_token(subject: str | int, claims: Dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": str(subject), "exp": expire, "type": "access"}
    if claims:
        to_encode.update(claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def encrypt_pdf_payload(data: bytes) -> bytes:
    """
    Encrypts a raw PDF binary using AES-256-GCM.
    Returns: 12-byte Nonce + Ciphertext (which includes the 16-byte GCM authentication tag).
    """
    nonce = os.urandom(12)  # Standard 96-bit nonce for GCM
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext


def decrypt_pdf_payload(payload: bytes) -> bytes:
    """
    Splits the 12-byte nonce from the encrypted stream and decrypts the payload.
    Raises InvalidTag if data was altered or tampered with.
    """
    if len(payload) < 28:  # 12 bytes nonce + 16 bytes tag minimum
        raise ValueError("Corrupted encrypted payload: buffer too short.")
    nonce = payload[:12]
    ciphertext = payload[12:]
    return aesgcm.decrypt(nonce, ciphertext, None)