from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import create_access_token, create_captcha, get_current_user, hash_password, verify_captcha, verify_password
from ..database import get_db
from ..limiter import limiter
from ..models import User
from ..schemas import TokenResponse, UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/captcha")
def get_captcha():
    return create_captcha()


@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit("3/minute")
def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    if not verify_captcha(data.captcha_token, data.captcha_answer):
        raise HTTPException(status_code=400, detail="验证码错误")
    existing = db.execute(select(User).where(User.username == data.username)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    if not verify_captcha(data.captcha_token, data.captcha_answer):
        raise HTTPException(status_code=400, detail="验证码错误")
    user = db.execute(select(User).where(User.username == data.username)).scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            points=user.points,
            created_at=user.created_at,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
