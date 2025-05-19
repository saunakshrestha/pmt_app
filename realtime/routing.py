from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path("ws/boards/<int:board_id>/", consumers.BoardConsumer.as_asgi()),
    # path("ws/comments/<int:task_id>/", consumers.CommentConsumer.as_asgi()),
    # path("ws/notifications/<int:user_id>/", consumers.NotificationConsumer.as_asgi()),
]