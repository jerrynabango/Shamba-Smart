from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/direct_message/<str:receiver_username>/',
         consumers.DirectMessageConsumer.as_asgi()),
]
