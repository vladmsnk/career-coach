import base64
import json
import hmac
import hashlib
import time
from datetime import timedelta

from app.core.settings import settings

ACCESS_TOKEN_EXPIRE_MINUTES = 30


def _b64encode(data: bytes) -> bytes:
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
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
