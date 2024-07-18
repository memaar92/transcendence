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

#shall we also use the picture from 42 as profile picture? 
def register42User(email, nickname):
    new_user = CustomUser(email=email, displayname=nickname, is_42_auth=True)
    new_user.save()

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

    print("user info: ", user_info)
    user = CustomUser.objects.filter(email=user_info['email']).values('email', 'is_42_auth') #use 42_id as identifier instead?
    print("user: ", user)
    if user.exists() and user.first()['is_42_auth'] == False:
        return HttpResponse("Wrong authentication method")
        #return Response({'detail': 'Wrong authentication method'}, status=status.HTTP_400_BAD_REQUEST)
    elif not user.exists():
        register42User(user_info['email'], user_info['login'])
    #return JWT access token
    
    return HttpResponse("Hello, world. You're at the 42 auth test2.") # create JWT access token and return it with JSON response (frontend as recipient) Should be same as with user registration


#class AuthWith42(APIView):
#    def get(self, request):
#        return Response(status=status.HTTP_204_NO_CONTENT)