from django.urls import path
from . import views

urlpatterns = [
    path('', views.live_chat, name='live_chat'),
    path('index.html', views.index, name='index'),
]