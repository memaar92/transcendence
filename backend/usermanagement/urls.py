from django.urls import path
from . import views

urlpatterns = [
	path('json/', views.json, name='json'),
]
