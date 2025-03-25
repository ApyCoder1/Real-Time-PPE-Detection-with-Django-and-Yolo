from django.urls import path
from app1 import views

urlpatterns = [
    
    path('', views.ppe_detection, name='ppe_detection-page'),  # URL to the PPE-Page
    path('detections/', views.detection_list, name='detection_list'),
    path('fetch-detections/', views.fetch_detections, name='fetch_detections'),
    
    
]
