from django.urls import path
from . import views

urlpatterns = [
	path('games/', views.GameHistoryList.as_view(), name='game-history-list'),
	path('users/<int:pk>/', views.UserView.as_view(), name='user-detail'),
	path('register/', views.CreateUserView.as_view(), name='register'),
	path('users/<int:pk>/change/', views.ChangeUserView.as_view(), name='change-user'),
	path('api/user/profilepicture/<int:pk>/', views.ProfilePictureView.as_view(), name='profile_picture'),
	path('api/user/profilepicture/<int:pk>/delete/', views.ProfilePictureDeleteView.as_view(), name='profile_picture_delete'),
]
