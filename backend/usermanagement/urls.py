from django.urls import path
from . import views

urlpatterns = [
	path('games/', views.GameHistoryList.as_view(), name='game-history-list'),
	path('users/<int:pk>/', views.UserView.as_view(), name='user-detail'),
	path('register/', views.CreateUserView.as_view(), name='register'),
	path('users/<int:pk>/edit/', views.EditUserView.as_view(), name='edit-user'),
]
