
from django.http import JsonResponse, Http404, HttpRequest, HttpResponse
from ninja.errors import ValidationError, HttpError
from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.conf import settings
import traceback, logging

logger = logging.getLogger("api")


from ninja.errors import HttpError

class UnauthorizedError(HttpError):
    def __init__(self, message="Authentication credentials were not provided or invalid."):
        super().__init__(401, message)

class ApiValidationError(Exception):
    def __init__(self, details, message="Validation failed", code="INVALID_INPUT"):
        self.details = details
        self.message = message
        self.code = code
        super().__init__(message)

def custom_api_validation_error(request, exc, *args, **kwargs):
    return JsonResponse({
        "success": False,
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    }, status=400)

# 400 - Input Validation error (from Ninja/Pydantic)
def custom_validation_error(request: HttpRequest, exc: ValidationError, *args, **kwargs) -> HttpResponse:
    logger.error(f"Validation error: {exc.errors}")
    errors = {}
    for err in exc.errors:
        loc = err.get("loc", [])
        msg = err.get("msg", "Invalid input")
        if loc == ("body", "payload"):
            errors.setdefault("non_field_errors", []).append("Payload is required.")
        else:
            field_path = ".".join(str(i) for i in loc if i not in ("body", "payload"))
            errors.setdefault(field_path or "non_field_errors", []).append(msg)
    return JsonResponse({
        "success": False,
        "error": {
            "code": "INVALID_INPUT",
            "message": "Validation failed",
            "details": errors
        }
    }, status=400)


# 400 - Django model form validation errors
def custom_django_validation_error(request: HttpRequest, exc: DjangoValidationError, *args, **kwargs) -> HttpResponse:
    logger.error(f"Django Validation error: {getattr(exc, 'message_dict', str(exc))}")
    details = getattr(exc, "message_dict", str(exc))
    return JsonResponse({
        "success": False,
        "error": {
            "code": "INVALID_INPUT",
            "message": "Validation failed",
            "details": details
        }
    }, status=400)


# 401 - Authentication errors (e.g. invalid or missing Bearer token)
class AuthenticationError(Exception):
    """Custom error for authentication failures."""
    def __init__(self, message="Authentication credentials were not provided or invalid."):
        self.message = message
        super().__init__(self.message)

def custom_401(request: HttpRequest, exc: Exception, *args, **kwargs) -> HttpResponse:
    return JsonResponse({
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": str(exc) or "Authentication credentials were not provided or invalid."
        }
    }, status=401)


# 403 - Permission denied/forbidden
def custom_403(request: HttpRequest, exc: PermissionDenied, *args, **kwargs) -> HttpResponse:
    return JsonResponse({
        "success": False,
        "error": {
            "code": "FORBIDDEN",
            "message": str(exc) or "You do not have permission to perform this action."
        }
    }, status=403)


# 404 - Resource not found
def custom_404(request: HttpRequest, exc: Http404, *args, **kwargs) -> HttpResponse:
    return JsonResponse({
        "success": False,
        "error": {
            "code": "NOT_FOUND",
            "message": str(exc) or "Resource not found"
        }
    }, status=404)


# 409 - Integrity error, e.g. unique constraint failed
def custom_integrity_error(request: HttpRequest, exc: IntegrityError, *args, **kwargs) -> HttpResponse:
    logger.error(f"IntegrityError: {exc}")
    msg = "Duplicate entry or integrity constraint violation."
    return JsonResponse({
        "success": False,
        "error": {
            "code": "CONFLICT",
            "message": msg,
            "details": {"non_field_errors": [str(exc)]}
        }
    }, status=409)


# 422 - Unprocessable entity (for special validation)
class UnprocessableEntityError(Exception):
    """Custom error for 422 Unprocessable Entity."""
    def __init__(self, message="The request was well-formed but could not be processed."):
        self.message = message
        super().__init__(self.message)

def custom_422(request: HttpRequest, exc: Exception, *args, **kwargs) -> HttpResponse:
    return JsonResponse({
        "success": False,
        "error": {
            "code": "UNPROCESSABLE_ENTITY",
            "message": str(exc) or "The request was well-formed but could not be processed."
        }
    }, status=422)


# 429 - Too many requests / throttling
class Throttled(Exception):
    """Custom error for 429 Too Many Requests."""
    def __init__(self, message="Request was throttled. Too many requests."):
        self.message = message
        super().__init__(self.message)

def custom_429(request: HttpRequest, exc: Exception, *args, **kwargs) -> HttpResponse:
    return JsonResponse({
        "success": False,
        "error": {
            "code": "TOO_MANY_REQUESTS",
            "message": str(exc) or "Request was throttled. Too many requests."
        }
    }, status=429)


def custom_http_error(request: HttpRequest, exc: HttpError, *args, **kwargs) -> HttpResponse:
    # Map HTTP status codes to string codes and default messages
    code_map = {
        400: ("BAD_REQUEST", "The request could not be understood or was missing required parameters."),
        401: ("UNAUTHORIZED", "Authentication credentials were missing or incorrect."),
        403: ("FORBIDDEN", "You do not have permission to perform this action."),
        404: ("NOT_FOUND", "The requested resource was not found."),
        405: ("METHOD_NOT_ALLOWED", "The method is not allowed for this endpoint."),
        409: ("CONFLICT", "A conflict occurred with the current state of the resource."),
        422: ("UNPROCESSABLE_ENTITY", "The request was well-formed but was unable to be followed due to semantic errors."),
        429: ("TOO_MANY_REQUESTS", "Request was throttled. Too many requests."),
        500: ("SERVER_ERROR", "An internal server error occurred. Please try again later.")
    }

    status_code = getattr(exc, "status_code", 400)
    code, default_msg = code_map.get(
        status_code, (f"HTTP_{status_code}", f"An error occurred (status {status_code}).")
    )

    # If the exception message is generic or empty, use the default message
    exc_msg = default_msg
    if settings.DEBUG and status_code == 500:
        exc_msg = str(exc) or default_msg

    # Optionally, for 401/403 you can hide technical details in production
    # if status_code in (401, 403) and not settings.DEBUG:
    #     exc_msg = default_msg

    return JsonResponse({
        "success": False,
        "error": {
            "code": code,
            "message": exc_msg
        }
    }, status=status_code)


# 500 - Any other error (server error)
def custom_general_error(request: HttpRequest, exc: Exception, *args, **kwargs) -> HttpResponse:
    logger.exception(exc)
    if settings.DEBUG:
        return JsonResponse({
            "success": False,
            "error": {
                "code": "SERVER_ERROR",
                "message": str(exc),
                "trace": traceback.format_exc()
            }
        }, status=500)
    return JsonResponse({
        "success": False,
        "error": {
            "code": "SERVER_ERROR",
            "message": "An unexpected error occurred"
        }
    }, status=500)

def custom_unauthorized_error(request, exc, *args, **kwargs):
    return JsonResponse({
        "success": False,
        "error": {
            "code": "UNAUTHORIZED",
            "message": str(exc)
        }
    }, status=401)

# Register all handlers with your NinjaAPI instance
def register_custom_exception_handlers(api):
    from ninja.errors import ValidationError, HttpError
    from django.core.exceptions import PermissionDenied, ValidationError as DjangoValidationError
    from django.http import Http404
    from django.db import IntegrityError

    # Standard and custom handlers
    api.add_exception_handler(ApiValidationError, custom_api_validation_error)
    api.add_exception_handler(ValidationError, custom_validation_error)      # 400 (Ninja validation)
    api.add_exception_handler(DjangoValidationError, custom_django_validation_error)  # 400 (Django forms/models)
    api.add_exception_handler(HttpError, custom_http_error)                  # 400/other (Ninja HTTPError)
    api.add_exception_handler(AuthenticationError, custom_401)               # 401
    api.add_exception_handler(PermissionDenied, custom_403)                  # 403
    api.add_exception_handler(Http404, custom_404)                           # 404
    api.add_exception_handler(IntegrityError, custom_integrity_error)        # 409
    api.add_exception_handler(UnprocessableEntityError, custom_422)          # 422
    api.add_exception_handler(Throttled, custom_429)                         # 429
    api.add_exception_handler(Exception, custom_general_error)               # 500 (fallback)

    api.add_exception_handler(UnauthorizedError, custom_unauthorized_error)
