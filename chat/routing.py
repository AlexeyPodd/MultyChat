from django.urls import re_path

from .consumers import ChatRoomConsumer


websocket_urlpatterns = [
    re_path(r'ws/room/(?P<chat_owner_slug>[-\w]+)/$', ChatRoomConsumer.as_asgi()),
]

