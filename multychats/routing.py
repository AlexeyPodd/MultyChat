from channels.routing import ProtocolTypeRouter

from .asgi import application as django_asgi_app, websocket_app


application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': websocket_app,
})
