from django.urls import path
from . import views

urlpatterns = [
    path('', views.layout, name='layout'),
    
    # Login URL
    path('login/', views.login_view, name='login'),
    
    # Logout URL
    path('logout/', views.logout_view, name='logout'),
    
    # Dynamically loaded content URLs
    path('home/', views.home_content, name='home_content'),
    path('about/', views.about_content, name='about_content')
]
