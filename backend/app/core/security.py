import base64
import hashlib
from secrets import token_urlsafe

from cryptography.fernet import Fernet

from app.core.config import get_settings


def generate_state_token() -> str:
    return token_urlsafe(32)


def _fernet_for_key(encryption_key: str) -> Fernet:
    digest = hashlib.sha256(encryption_key.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: str, encryption_key: str | None = None) -> str:
    key = encryption_key or get_settings().app_encryption_key
    return _fernet_for_key(key).encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str, encryption_key: str | None = None) -> str:
    key = encryption_key or get_settings().app_encryption_key
    return _fernet_for_key(key).decrypt(value.encode("utf-8")).decode("utf-8")
