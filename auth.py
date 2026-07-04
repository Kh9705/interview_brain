from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

import config
from database import get_db
from models import AuthResponse, LoginRequest, RegisterRequest

router = APIRouter(prefix="/api", tags=["auth"])

security_scheme = HTTPBearer()


def _hash_password(password: str) -> str:
    pwd = password.encode("utf-8")[:72]
    return _bcrypt.hashpw(pwd, _bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain: str, hashed: str) -> bool:
    pwd = plain.encode("utf-8")[:72]
    return _bcrypt.checkpw(pwd, hashed.encode("utf-8"))


def _create_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_EXPIRATION_MINUTES)
    payload = {"sub": user_id, "email": email, "exp": expire}
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


# ── Dependency ───────────────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> dict:
    """Decode the JWT and return the full user row from SQLite."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {
        "id": row["id"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "companies": json.loads(row["companies"]),
        "weak_areas": json.loads(row["weak_areas"]),
        "created_at": row["created_at"],
    }


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest):
    db = await get_db()

    # Check for duplicate email
    cursor = await db.execute("SELECT id FROM users WHERE email = ?", (body.email,))
    if await cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        """INSERT INTO users (id, email, name, password_hash, role, companies, weak_areas, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            body.email,
            body.name,
            _hash_password(body.password),
            body.role,
            json.dumps(body.companies),
            json.dumps(body.weak_areas),
            now,
        ),
    )
    await db.commit()

    token = _create_token(user_id, body.email)
    return AuthResponse(access_token=token, user_id=user_id, name=body.name, email=body.email)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    db = await get_db()
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (body.email,))
    row = await cursor.fetchone()

    if row is None or not _verify_password(body.password, row["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = _create_token(row["id"], row["email"])
    return AuthResponse(access_token=token, user_id=row["id"], name=row["name"], email=row["email"])
