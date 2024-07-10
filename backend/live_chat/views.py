from django.shortcuts import render

# Create your views here.
def live_chat(request):
    context = {'sender_id': request.user.id}
    return render(request, 'live_chat.html')