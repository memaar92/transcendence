from django.shortcuts import render
from django.http import HttpResponse

def json(request):
    return render(request, 'json.json')
