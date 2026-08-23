# ============================================================
# auth_service/main.py
# Auth Service — JWT creation and verification
# Port: 8001
# ============================================================

import os
import time
import uuid
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Try jose for JWT, fall back to simple base64 mock
try:
    from jose import jwt, JWTError
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    import base64, json

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from shared.tracing import RequestTracingMiddleware, ServiceLogger

log = ServiceLogger("auth-service")

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-prod")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 30

# In-memory user store (replace with real DB in production)
USERS_DB = {
    "humayun": {
        "user_id": "user-001",
        "password_hash": "hashed_password_123",    # In prod: bcrypt
        "role": "admin",
        "email": "humayun@example.com"
    },
    "demo": {
        "user_id": "user-002",
        "password_hash": "demo_password",
        "role": "user",
        "email": "demo@example.com"
    }
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Auth Service starting on port 8001")
    log.info(f"JWT_AVAILABLE={JWT_AVAILABLE}, algorithm={JWT_ALGORITHM}")
    yield
    log.info("Auth Service shutting down")


app = FastAPI(
    title="Auth Service",
    description="JWT authentication — microservice #1",
    version="1.0.0",
    lifespan=lifespan
)
app.add_middleware(RequestTracingMiddleware, service_name="auth-service")


# ─── Schemas ─────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str    # In prod: hash and compare with bcrypt

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_MINUTES * 60
    user_id: str
    role: str

class VerifyRequest(BaseModel):
    token: str

class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str
    email: str


# ─── Token helpers ────────────────────────────────────────────

def create_token(user_id: str, username: str, role: str) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_MINUTES),
        "jti": str(uuid.uuid4())[:8]
    }
    if JWT_AVAILABLE:
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    else:
        # Simple base64 mock (NOT for production)
        return base64.b64encode(json.dumps({
            **payload,
            "iat": payload["iat"].isoformat(),
            "exp": payload["exp"].isoformat()
        }).encode()).decode()


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT. Returns payload or None."""
    try:
        if JWT_AVAILABLE:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        else:
            import base64, json
            data = json.loads(base64.b64decode(token.encode()).decode())
            # Check expiry
            from datetime import datetime
            exp = datetime.fromisoformat(data["exp"])
            if datetime.utcnow() > exp:
                return None
            return data
    except Exception:
        return None


# ─── Endpoints ────────────────────────────────────────────────

@app.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest) -> TokenResponse:
    """Login and receive a JWT access token."""
    user = USERS_DB.get(request.username)
    if not user:
        log.warning(f"Login failed: unknown user '{request.username}'")
        raise HTTPException(401, "Invalid credentials")

    # In production: bcrypt.checkpw(password, stored_hash)
    if request.password not in ("password", "demo_password", "hashed_password_123"):
        log.warning(f"Login failed: wrong password for '{request.username}'")
        raise HTTPException(401, "Invalid credentials")

    token = create_token(user["user_id"], request.username, user["role"])
    log.info(f"Login successful: {request.username} (role={user['role']})")

    return TokenResponse(
        access_token=token,
        user_id=user["user_id"],
        role=user["role"]
    )


@app.post("/auth/verify")
def verify(request: VerifyRequest) -> dict:
    """
    Verify a JWT token.

    Called by other services to authenticate requests.
    Returns user info if valid, 401 if invalid.
    """
    payload = decode_token(request.token)
    if not payload:
        log.warning("Token verification failed")
        raise HTTPException(401, "Invalid or expired token")

    log.info(f"Token verified for user {payload.get('username', '?')}")
    return {
        "valid": True,
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role"),
        "expires": payload.get("exp") if isinstance(payload.get("exp"), str)
                   else None
    }


@app.get("/auth/users", summary="List users (demo only)")
def list_users() -> dict:
    """Return public user info (no passwords)."""
    return {
        "users": [
            {"username": uname, "user_id": u["user_id"],
             "role": u["role"], "email": u["email"]}
            for uname, u in USERS_DB.items()
        ]
    }


@app.get("/health")
def health() -> dict:
    return {
        "service": "auth-service",
        "status": "healthy",
        "port": 8001,
        "jwt_available": JWT_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
def root() -> dict:
    return {
        "service": "auth-service",
        "version": "1.0.0",
        "endpoints": {
            "login": "POST /auth/login",
            "verify": "POST /auth/verify",
            "health": "GET /health"
        }
    }