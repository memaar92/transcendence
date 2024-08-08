from django.urls import path
from . import views

urlpatterns = [
	#path('', views.auth42, name='auth_42'),
	path('', views.AuthWith42View.as_view(), name='auth_42'),
	#path('redirect/', views.redirect42, name='redirect42'),
	path('redirect/', views.Redirect42Auth.as_view(), name='redirect42'),
]