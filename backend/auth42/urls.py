from django.urls import path
from . import views

urlpatterns = [
	path('', views.auth42, name='auth_42'),
	path('redirect/', views.redirect42, name='redirect42'),
]