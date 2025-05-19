from asgiref.local import Local

_thread_locals = Local()

def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)

class CurrentUserMiddleware:
    """
    Middleware to store the current user in a thread/coroutine-local variable.
    Add to your MIDDLEWARE setting after AuthenticationMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        try:
            response = self.get_response(request)
        finally:
            _thread_locals.user = None  # Ensure cleanup after request
        return response

# For Django Channels/consumers (WebSockets):
def set_current_user(user):
    """
    Manually set the current user (for WebSocket consumers).
    """
    _thread_locals.user = user

def clear_current_user():
    """
    Clear the current user (for WebSocket consumers).
    """
    _thread_locals.user = None