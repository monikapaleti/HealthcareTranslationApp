from django.urls import path
from . import views
urlpatterns = [
    path('', views.translate_and_audio, name='translate_and_audio'),
    path('upload-audio/', views.upload_audio, name='upload_audio'),
]