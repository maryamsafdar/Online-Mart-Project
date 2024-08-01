from passlib.context import CryptContext
from sqlmodel import Session, select
from typing import Annotated, Optional
from app.deps import get_session
from fastapi import Depends, HTTPException, status
from app.models.user_model import TokenData, User
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from datetime import datetime, timezone, timedelta

SECRET_KEY = 'ed60732905aeb0315e2f77d05a6cb57a0e408eaf2cb9a77a5a2667931c50d4e0'
ALGORITHM = 'HS256'
EXPIRY_TIME = 10

oauth_scheme = OAuth2PasswordBearer(tokenUrl="/token")

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(password: str) -> str:
    """Hash a password for storing."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against one provided by user."""
    return pwd_context.verify(plain_password, hashed_password)

def get_user_from_db(session: Annotated[Session, Depends(get_session)], username: str | None = None, email: str | None = None):
    statement = select(User).where(User.username == username)
    user = session.exec(statement).first()
    if not user:
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
    return user

def authenticate_user(username: str, password: str, session: Session) -> Optional[User]:
    user = get_user_from_db(session, username, None)
    print(f"Authenticating user: {username}, {password}")
    if not user:
        print("User not found")
    if not verify_password(password, user.password):
        print("Password verification failed")
    if not user or not verify_password(password, user.password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, ALGORITHM)

async def current_user(token: Annotated[str, Depends(oauth_scheme)], session: Annotated[Session, Depends(get_session)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = get_user_from_db(session, username=token_data.username)
    if not user:
        raise credentials_exception
    return user
