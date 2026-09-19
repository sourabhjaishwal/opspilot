import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.token import blacklist_token
from app.models.user import User
from app.routes.deps import get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer()


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, username=user.username, role=user.role)


def _validate_user_payload(username: str, password: str, role: str | None = None) -> tuple[str, str, str | None]:
    clean_username = username.strip()
    if not clean_username:
        logger.warning("Auth validation failed: username is empty")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is required.")
    if not password or not password.strip():
        logger.warning("Auth validation failed: empty password for username=%s", clean_username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password is required.")
    if len(password) < 8:
        logger.warning("Auth validation failed: weak password for username=%s", clean_username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 8 characters long.")
    if role is not None and role not in {"user", "admin"}:
        logger.warning("Auth validation failed: invalid role=%s for username=%s", role, clean_username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be either 'user' or 'admin'.")
    return clean_username, password, role


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    username, password, role = _validate_user_payload(user_data.username, user_data.password, user_data.role)
    existing_user = db.scalar(select(User).where(User.username == username))
    if existing_user is not None:
        logger.warning("Registration failed: duplicate username=%s", username)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists. Please choose a different username.",
        )

    user = User(
        username=username,
        hashed_password=hash_password(password),
        role=role or "user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("User registered successfully: username=%s role=%s", user.username, user.role)
    return TokenResponse(
        access_token=create_access_token(user.id, user.username, user.role),
        user=_user_response(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    username, password, _ = _validate_user_payload(credentials.username, credentials.password)
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        logger.warning("Login failed: unknown user=%s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    if not verify_password(password, user.hashed_password):
        logger.warning("Login failed: incorrect password for username=%s", username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    logger.info("User logged in successfully: username=%s role=%s", user.username, user.role)
    return TokenResponse(
        access_token=create_access_token(user.id, user.username, user.role),
        user=_user_response(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: User = Depends(get_current_user),
) -> None:
    del current_user
    blacklist_token(credentials.credentials)
    logger.info("User logged out successfully: token blacklisted")
