from django.urls import path
from . import views

urlpatterns = [
	path('init/', views.index, name='42auth_init'),
	path('', views.index2, name='42auth'),
	path('test/', views.test, name='42auth_test'),
]