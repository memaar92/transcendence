from django.shortcuts import render

# Create your views here.
def live_chat(request):
    return render(request, 'live_chat.html')

def index(request):
    return render(request, 'index.html')