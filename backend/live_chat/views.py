from django.shortcuts import render

# Create your views here.
def live_chat(request):
    return render(request, 'live_chat.html')