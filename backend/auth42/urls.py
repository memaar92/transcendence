from django.urls import path
from . import views

urlpatterns = [
	path('', views.AuthWith42.as_view(), name='42auth'),
]