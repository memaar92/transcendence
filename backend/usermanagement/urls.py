from django.urls import path
from . import views

urlpatterns = [
	path('games/', views.GameHistoryList.as_view(), name='game-history-list'),
	path('register/', views.CreateUserView.as_view(), name='register'),
	path('users/<int:pk>/', views.UserView.as_view(), name='user-detail'),
	#path('users/<int:pk>/edit/', views.EditUserView.as_view(), name='edit-user'),
	path('profile/', views.EditUserView.as_view(), name='edit-user'),
	#path('users/<int:pk>/delete_picture/', views.ProfilePictureDeleteView.as_view(), name='delete-user_picture'),
	path('profile/delete_picture/', views.ProfilePictureDeleteView.as_view(), name='delete-user_picture'),
	#TODO: delete verify view, just for debugging
	path('2fa/verify/', views.TOTPVerifyView.as_view(), name='2fa_verify'),
	path('2fa/setup/', views.TOTPSetupView.as_view(), name='2fa_setup'),
	path('token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
	path('email/', views.CheckEmail.as_view(), name='check_email'),
	path('email/validate/', views.ValidateEmailView.as_view(), name='validate_email'),
	path('email/otp/', views.GenerateOTPView.as_view(), name='email_otp'),
	path('token/logout/', views.LogoutView.as_view(), name='logout'),
]
