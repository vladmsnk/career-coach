from dataclasses import dataclass


@dataclass
class User:
    id: str
    login: str
    email: str
    password_hash: str



