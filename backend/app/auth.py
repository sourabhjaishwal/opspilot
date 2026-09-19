import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import HTTPException, status
from app.config import get_settings

_HASH_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _HASH_ITERATIONS)
    return f"pbkdf2_sha256${_HASH_ITERATIONS}${_encode(salt)}${_encode(digest)}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), _decode(salt), int(iterations)
        )
        return hmac.compare_digest(digest, _decode(expected))
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, username: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + get_settings().access_token_expire_minutes * 60,
    }
    header = {"alg": "HS256", "typ": "JWT"}
    encoded_header = _encode_json(header)
    encoded_payload = _encode_json(payload)
    signature = _sign(f"{encoded_header}.{encoded_payload}")
    return f"{encoded_header}.{encoded_payload}.{signature}"


def decode_access_token(token: str) -> dict[str, object]:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        encoded_header, encoded_payload, signature = token.split(".")
        if not hmac.compare_digest(signature, _sign(f"{encoded_header}.{encoded_payload}")):
            raise unauthorized
        header = json.loads(_decode(encoded_header))
        payload = json.loads(_decode(encoded_payload))
        if header.get("alg") != "HS256" or int(payload["exp"]) <= int(time.time()):
            raise unauthorized
        return payload
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise unauthorized from exc


def _sign(value: str) -> str:
    secret = get_settings().jwt_secret.encode()
    digest = hmac.new(secret, value.encode(), hashlib.sha256).digest()
    return _encode(digest)


def _encode_json(value: dict[str, object]) -> str:
    return _encode(json.dumps(value, separators=(",", ":")).encode())


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
