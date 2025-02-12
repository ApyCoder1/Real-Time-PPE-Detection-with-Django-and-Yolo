from django.urls import path
from app1 import views

urlpatterns = [
    
    path('', views.yolo, name='yolo-page'),  # URL to the YoloPage
    
    
]
