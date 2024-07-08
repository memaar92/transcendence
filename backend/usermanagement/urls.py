from django.urls import path
from . import views

urlpatterns = [
	path('json/', views.json, name='json'),
	path('games/', views.GameHistoryList.as_view(), name='game-history-list'),
	path('users/<int:pk>/', views.UserView.as_view(), name='user-detail'),
]
