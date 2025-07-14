import secrets

from passlib.context import CryptContext


def gen_id(size: int = 32) -> str:
    return secrets.token_urlsafe(size)


def gen_otp(length: int = 8):
    otp = "".join([str(secrets.randbelow(10)) for _ in range(length)])
    return otp


def hash_password(password: str):
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return password_context.verify(plain_password, hashed_password)
