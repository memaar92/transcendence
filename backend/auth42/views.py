from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseBadRequest
from usermanagement.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
import requests
import json

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
    if CustomUser.objects.filter(displayname=nickname).exists():
        id = CustomUser.objects.filter(displayname__istartswith = nickname).count()
        nickname = nickname + "_" + str(id)
    new_user = CustomUser(email=email, displayname=nickname, is_42_auth=True)
    new_user.save()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

def auth42(request):
    if (code := request.GET.get('code')) is None:
        return HttpResponseBadRequest("42auth failed: no code provided")
    code = request.GET.get('code')
    oauth_response = requests.post('https://api.intra.42.fr/oauth/token', data={
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': get_secret('oauth_client_id'),
        'client_secret': get_secret('oauth_secret'),
        'redirect_uri': 'https://localhost/42auth'
    }).json()
    if (oauth_response.get('error')):
        return HttpResponseBadRequest("42auth failed: " + oauth_response['error'])
    user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
        'Authorization': 'Bearer ' + oauth_response['access_token']
    }).json()

    user = CustomUser.objects.filter(email=user_info['email']).values('email', 'is_42_auth') #use 42_id as identifier instead?
    if user.exists() and user.first()['is_42_auth'] == False:
        return HttpResponseBadRequest("Wrong authentication method")
    elif not user.exists():
        register42User(user_info['email'], user_info['login'])
    
    token = get_tokens_for_user(CustomUser.objects.get(email=user_info['email']))
    return HttpResponse(json.dumps(token), content_type='application/json', status=200, headers={'Vary': 'Accept'})
