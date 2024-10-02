from django.shortcuts import render

# Create your views here.
def pong(request):
    return render(request, 'pong.html')

def tournament(request):
    return render(request, 'tournament.html')