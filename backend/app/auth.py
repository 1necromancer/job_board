from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/admin/login", auto_error=False)

# Hash the admin password once on startup so we never store plaintext anywhere.
_ADMIN_HASH: str | None = None


def _admin_hash() -> str:
    global _ADMIN_HASH
    if _ADMIN_HASH is None:
        _ADMIN_HASH = pwd_ctx.hash(settings.ADMIN_PASSWORD)
    return _ADMIN_HASH


def verify_admin_password(plain: str) -> bool:
    return pwd_ctx.verify(plain, _admin_hash())


def create_access_token(subject: str = "admin") -> tuple[str, int]:
    expires_in = settings.JWT_EXPIRES_MINUTES * 60
    expire = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    payload = {"sub": subject, "exp": expire, "role": "admin"}
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def require_admin(token: str | None = Depends(oauth2_scheme)) -> str:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise cred_exc
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("role") != "admin":
            raise cred_exc
        return payload.get("sub", "admin")
    except JWTError as e:
        raise cred_exc from e
