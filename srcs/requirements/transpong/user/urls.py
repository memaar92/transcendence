from django.urls import path
from . import views

urlpatterns = [
    path('', views.layout, name='layout'),
    
    path('profile/', views.profile, name='profile'),
	path('json/', views.json, name='json'),

    path('login/', views.login, name='login'),
    path('login_check/', views.login_check, name='login_check'),
    
    path('logout/', views.logout_view, name='logout'),

    path('home/', views.home_content, name='home_content'),
    path('about/', views.about_content, name='about_content')
]
