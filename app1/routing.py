from django.urls import path
from .consumers import VideoStreamConsumer

websocket_urlpatterns = [
   
    path('ws/video_stream/',VideoStreamConsumer.as_asgi()),
]
