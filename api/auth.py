import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from config import settings
from mysite import SessionLocal
from mysite import RefreshToken, User, UserStatus
from mysite import TokenResponse, UserCreate, UserLogin, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()
TokenType = Literal["access", "refresh"]

auth_router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)


def create_token(user_id: int, token_type: TokenType):
    if token_type == "access":
        lifetime = timedelta(minutes=settings.ACCESS_TOKEN_LIFETIME)
    else:
        lifetime = timedelta(days=settings.REFRESH_TOKEN_LIFETIME)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "exp": datetime.now(timezone.utc) + lifetime,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, expected_type: TokenType) -> int:
    """user_id кайтарат, ар кандай көйгөйдө ValueError."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            raise ValueError("wrong token type")
        return int(payload["sub"])
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise ValueError("invalid token") from exc


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    exc = HTTPException(
        status_code=401,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_token(creds.credentials, "access")
    except ValueError:
        raise exc
    user = db.get(User, user_id)
    if user is None:
        raise exc
    return user


def require_roles(*roles: UserStatus):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.status not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

    return checker


def _digest(token: str):
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_tokens(user_id: int):
    return create_token(user_id, "access"), create_token(user_id, "refresh")


@auth_router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    exists = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Email or username already registered")

    db_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        status=user.status,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@auth_router.post("/login", response_model=TokenResponse)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access, refresh = _issue_tokens(db_user.id)
    db.add(RefreshToken(user_id=db_user.id, token=_digest(refresh)))
    db.commit()
    return TokenResponse(access_token=access, refresh_token=refresh)


@auth_router.post("/logout")
def logout(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    stored = db.query(RefreshToken).filter(RefreshToken.token == _digest(refresh_token)).first()
    if not stored:
        raise HTTPException(status_code=401, detail="Invalid token")
    db.delete(stored)
    db.commit()
    return {"message": "Successfully logged out"}


@auth_router.post("/refresh", response_model=TokenResponse)
def refresh(refresh_token: str = Body(..., embed=True), db: Session = Depends(get_db)):
    invalid = HTTPException(status_code=401, detail="Invalid token")
    try:
        user_id = decode_token(refresh_token, "refresh")
    except ValueError:
        raise invalid

    stored = db.query(RefreshToken).filter(
        RefreshToken.token == _digest(refresh_token),
        RefreshToken.user_id == user_id,
    ).first()
    if not stored:
        raise invalid

    access, new_refresh = _issue_tokens(user_id)
    stored.token = _digest(new_refresh)
    db.commit()
    return TokenResponse(access_token=access, refresh_token=new_refresh)


@auth_router.get("/me", response_model=UserResponse)
def user_me(profile: User = Depends(get_current_user)):
    return profile


@auth_router.get("/verify")
def verify_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "status": current_user.status,
    }