import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate JWT, return User ORM object."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.get(User, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role, raises 403 otherwise."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


CAPTCHA_EXPIRE = 5  # minutes


def create_captcha() -> dict:
    """Generate a math CAPTCHA question and a short-lived JWT token with the answer."""
    a = random.randint(1, 9)
    b = random.randint(1, 9)
    if random.choice([True, False]):
        op = "+"
        answer = a + b
    else:
        # Ensure result > 0
        if a < b:
            a, b = b, a
        op = "-"
        answer = a - b
    question = f"{a} {op} {b} = ?"
    token = create_access_token(
        data={"answer": answer},
        expires_delta=timedelta(minutes=CAPTCHA_EXPIRE),
    )
    return {"token": token, "question": question}


def verify_captcha(captcha_token: Optional[str], captcha_answer: Optional[int]) -> bool:
    """Verify the captcha answer against the token. Returns True if valid or not provided."""
    if not captcha_token:
        return True  # backward compat
    try:
        payload = jwt.decode(captcha_token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        expected = payload.get("answer")
        return expected is not None and expected == captcha_answer
    except JWTError:
        return False
