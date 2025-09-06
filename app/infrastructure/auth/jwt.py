import base64
import json
import hmac
import hashlib
import time
from datetime import timedelta
from typing import Optional

from app.core.settings import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _b64encode(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    expire = int(time.time() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).total_seconds())
    payload = {"sub": subject, "exp": expire}
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = b".".join([header_b64, payload_b64])
    signature = _b64encode(
        hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
    )
    return b".".join([signing_input, signature]).decode()


def decode_access_token(token: str) -> Optional[str]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected_sig = _b64encode(
            hmac.new(settings.secret_key.encode(), signing_input, hashlib.sha256).digest()
        ).decode()
        if not hmac.compare_digest(signature_b64, expected_sig):
            return None
        payload = json.loads(_b64decode(payload_b64))
        if payload.get("exp") < int(time.time()):
            return None
        return payload.get("sub")
    except Exception:
        return None
