from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from src.config.settings import AUTH_SECRET_KEY, AUTH_TOKEN_EXPIRE_HOURS


ALGORITHM = "HS256"


def create_admin_token(admin_data: dict) -> str:
    now = datetime.now(timezone.utc)
    expired_at = now + timedelta(hours=AUTH_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": str(admin_data["id"]),
        "username": admin_data.get("username"),
        "full_name": admin_data.get("full_name"),
        "role": admin_data.get("role", "admin"),
        "iat": int(now.timestamp()),
        "exp": int(expired_at.timestamp()),
    }

    return jwt.encode(payload, AUTH_SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_token(token: str) -> Optional[dict]:
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            AUTH_SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        return {
            "id": int(payload["sub"]),
            "username": payload.get("username"),
            "full_name": payload.get("full_name"),
            "role": payload.get("role", "admin"),
            "is_active": True,
        }

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None