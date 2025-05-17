
from ninja.security import HttpBearer
from ninja.errors import  HttpError
import jwt
from django.contrib.auth import get_user_model
from django.conf import settings

from accounts.api.v1.utils.exceptions import UnauthorizedError

User = get_user_model()

class JWTAuth(HttpBearer):
    def authenticate(self, request, token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                return UnauthorizedError("Missing user_id in token")
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return HttpError(401, "Invalid user")
            request.user = user  # Attach to request (like Django/DRF)
            request.jwt_payload = payload  # Optional: add the payload
            return user
        except jwt.ExpiredSignatureError:
            raise HttpError(401, "Token expired")
        except jwt.InvalidTokenError:
            raise HttpError(401, "Invalid token")