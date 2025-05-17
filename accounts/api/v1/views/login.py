import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from ninja import Router
from ..utils.exceptions import AuthenticationError
from accounts.api.v1.schemas.login import *
# from starlette import status

from ..utils.response import api_response

router = Router()

JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(hours=24)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


@router.post("/token", response=TokenResponse)
def token_create(request, data: TokenInput):
    user = authenticate(email=data.email, password=data.password)
    if not user:
        raise AuthenticationError(message="Invalid credentials")

    now = datetime.now()
    access_payload = {
        "user_id": user.id,
        "exp": now + ACCESS_TOKEN_LIFETIME,
        "type": "access"
    }
    refresh_payload = {
        "user_id": user.id,
        "exp": now + REFRESH_TOKEN_LIFETIME,
        "type": "refresh"
    }
    access = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    refresh = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return api_response(
        data={
            "access": access,
            "refresh": refresh
        },
        message="Token created successfully"
    )

@router.post("/token/refresh", response=TokenOnlyResponse)
def token_refresh(request, data: RefreshInput):
    try:
        payload = jwt.decode(data.refresh, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise AuthenticationError("Not a refresh token")
        user_id = payload.get("user_id")
        now = datetime.now()
        access_payload = {
            "user_id": user_id,
            "exp": now + ACCESS_TOKEN_LIFETIME,
            "type": "access"
        }
        access = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return {"access": access}
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Refresh token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid refresh token")

@router.post("/token/verify")
def token_verify(request, data: VerifyInput):
    try:
        payload = jwt.decode(data.token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return {"valid": True, "token_type": payload.get("type"), "user_id": payload.get("user_id")}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "detail": "Token expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "detail": "Invalid token"}