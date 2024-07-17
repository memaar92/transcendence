from django.shortcuts import render, redirect
from django.http import HttpResponse
from rest_framework import generics, status
from django.views import generic
from rest_framework.response import Response
from rest_framework.views import APIView
from usermanagement.models import CustomUser
import requests

# create more elegant way to get secrets as function is used in multiple places (e.g. settings.py)
def get_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}') as secret_file:
            return secret_file.read().strip()
    except IOError as e:
            raise Exception(f'Critical error reading secret {secret_name}: {e}')

def redirect42(request):
    target_url = 'https://api.intra.42.fr/oauth/authorize?client_id=' + get_secret('oauth_client_id') + '&redirect_uri=https%3A%2F%2Flocalhost%2F42auth&response_type=code'
    return redirect(target_url)

def auth42(request):
    if (code := request.GET.get('code')) is None:
        return HttpResponseBadRequest()
    code = request.GET.get('code')
    oauth_response = requests.post('https://api.intra.42.fr/oauth/token', data={
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': get_secret('oauth_client_id'),
        'client_secret': get_secret('oauth_secret'),
        'redirect_uri': 'https://localhost/42auth'
    }).json()
    print("oauth response: ", oauth_response)
    #error handling for oauth response
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + oauth_response['access_token']
    }).json()

    #print("user info: ", user_info)
    if CustomUser.objects.filter(email=user_info['email']).exists():
        print("user is in database")
    else:
        print("user is not in database")
    

    #check if user is already in database (based on 42_id?)
    #if already in database, no need to register
    #else: create new database entry (can I call a function from usermanagement.views here?)
    return HttpResponse("Hello, world. You're at the 42 auth test2.") # create JWT access token and return it with JSON response (frontend as recipient) Should be same as with user registration


#class AuthWith42(APIView):
#    def get(self, request):
#        return Response(status=status.HTTP_204_NO_CONTENT)