from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout

def user(request):
    # Render the main page
    return render(request, 'layout.html')

def layout(request):
    # Render the main page
    return render(request, 'layout.html')

def login_view(request):
    # Handle login logic
    username = request.POST.get('username')
    password = request.POST.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return redirect('login_view')
    else:
        # Return an 'invalid login' error message
        return redirect('inlogin_viewdex')

def logout_view(request):
    logout(request)
    return redirect('index')

def home_content(request):
    # Return HTML content for the 'home' section
    return render(request, 'home_content.html')

def about_content(request):
    # Return HTML content for the 'about' section
    return render(request, 'about_content.html')

# Add more views for other content sections as needed