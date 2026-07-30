# Day 22 — Authentication & Authorization: JWT, OAuth2 & RBAC

> **Phase 2 — Web Development** | Week 4 | Day 22 of 180

---

## 📌 What I Learned Today

- Why plain text passwords are catastrophic — rainbow table attacks
- bcrypt — intentionally slow password hashing with random salt
- CryptContext from passlib — hash and verify passwords
- JWT structure: header.payload.signature
- JWT claims: sub, exp, iat, jti (JWT ID for revocation)
- Access tokens (30 min) vs refresh tokens (7 days)
- python-jose library for JWT encoding and decoding
- create_access_token with custom expiry and extra claims
- decode_token — verify signature, expiry, and algorithm
- OAuth2PasswordBearer — FastAPI security scheme
- OAuth2PasswordRequestForm — form data for login
- get_current_user dependency — extract user from JWT
- Stateless auth — no database hit to verify tokens
- Token blacklist with Redis for logout functionality
- Timing attacks — dummy hash to prevent username enumeration
- RBAC — require_role() dependency factory with role hierarchy
- Token refresh flow — one-time use refresh tokens
- type claim in JWT to distinguish access vs refresh tokens
- auto_error=False for optional auth dependencies
- Security audit logging with background tasks
- Password strength validation with Pydantic validators
- Annotated type aliases: CurrentUser, AdminUser, EditorUser
- JWT revocation with Redis SETEX (TTL matches token expiry)

## 🔨 Project Built

**Task Manager Auth System** — Complete production auth:

- POST /auth/register — bcrypt password hashing, duplicate detection
- POST /auth/login — OAuth2 form data, returns access + refresh tokens
- POST /auth/login/json — JSON body alternative for non-browser clients
- POST /auth/refresh — validates refresh token, issues new access token
- POST /auth/logout — revokes access token in Redis blacklist
- GET /auth/me — decode JWT, check blacklist, return user profile
- PUT /auth/change-password — verify old, hash new, update DB
- All existing task/project endpoints now require Authorization: Bearer
- Role checks: admin for hard delete, editor for updates
- Optional auth with get_current_user_optional
- Security audit log: every auth event logged with timestamp
- Redis blacklist: revoked tokens rejected until natural expiry
- Timing-safe authentication: same response time for invalid user vs wrong password

## 🚀 How to Run

```bash
cd Day-22-FastAPI-Auth
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your settings
# Generate SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"

alembic upgrade head
python seed.py

uvicorn app.main:app --reload

# Open: http://localhost:8000/docs
# Click Authorize → username: humayun, password: password123
```

## 🧠 Auth Flow Summary

```
1. Register: POST /auth/register → creates user with bcrypt hash
2. Login:    POST /auth/login → returns access_token + refresh_token
3. Use API:  Authorization: Bearer <access_token> on every request
4. Expire:   Access token expires in 30 minutes
5. Refresh:  POST /auth/refresh with refresh_token → new access_token
6. Logout:   POST /auth/logout → revokes token in Redis blacklist
```

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
