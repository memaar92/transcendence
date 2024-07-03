from django.shortcuts import render

def json(request):
    return render(request, 'json.json')
