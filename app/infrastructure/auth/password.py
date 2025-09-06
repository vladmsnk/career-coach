import base64
import hashlib
import hmac
import os


class PasswordHasher:
    def hash(self, password: str) -> str:
        salt = os.urandom(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return base64.b64encode(salt + hashed).decode()

    def verify(self, password: str, password_hash: str) -> bool:
        data = base64.b64decode(password_hash.encode())
        salt, hashed = data[:16], data[16:]
        new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return hmac.compare_digest(hashed, new_hash)
