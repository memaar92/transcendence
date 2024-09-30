from django.urls import path
from pong import views

urlpatterns = [
    path('', views.pong, name='pong'),
]