from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics
from django.views import generic
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import redirect
import requests

def get_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}') as secret_file:
            return secret_file.read().strip()
    except IOError as e:
            raise Exception(f'Critical error reading secret {secret_name}: {e}')

def index(request):
    return redirect('https://api.intra.42.fr/oauth/authorize?client_id=u-s4t2ud-a2e745a099029f6f35be3df957c45817c6692892087079ba929ccc3610b635c3&redirect_uri=https%3A%2F%2Flocalhost%2F42auth&response_type=code')

def index2(request):
    code = request.GET.get('code')
    response = requests.post('https://api.intra.42.fr/oauth/token', data={
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': get_secret('oauth_client_id'),
        'client_secret': get_secret('oauth_secret'),
        'redirect_uri': 'https://localhost/42auth'
    }).json()
    print("oauth_response: ", response)
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + response['access_token']
    }).json()
    print("user info: ", user_info)
    return HttpResponse("Hello, world. You're at the 42 auth test2.") # create access token and return it

def test(request):
    return HttpResponse("Hello, world. You're at the 42 auth test.")


#class AuthWith42(APIView):
#    def get(self, request):
#        return Response(status=status.HTTP_204_NO_CONTENT)