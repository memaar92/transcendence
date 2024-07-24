from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseBadRequest
from usermanagement.models import CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from usermanagement.utils import random_filename
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

#is there a better way to do this? / potentially creates an issue with the username being too long (as max_size is 20)
def generateUniqueUsername(username):
    id = CustomUser.objects.filter(displayname__istartswith = username).count()
    while CustomUser.objects.filter(displayname= username + "_" + str(id)).exists():
        id += 1
    username = username + "_" + str(id)
    return username

def getProfilePicture(picture_url):
    image_req = requests.get(picture_url)
    if image_req.status_code != 200:
        return f"profile_pics/default.png"
    else:
        filename = random_filename(None, picture_url)
        filepath = settings.MEDIA_ROOT + f'/{filename}'
        try:
            with open(filepath, 'wb') as fp:
                fp.write(image_req.content)
        except IOError:
            return f"profile_pics/default.png"
    return filename

def register42User(email, username, picture_url):
    if CustomUser.objects.filter(displayname=username).exists():
        username = generateUniqueUsername(username)
    picture_name = getProfilePicture(picture_url)
    new_user = CustomUser(email=email, displayname=username, is_42_auth=True, profile_picture=picture_name)
    new_user.save()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

'''
class AuthWith42View(View):
    def get(self, request):
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
            register42User(user_info['email'], user_info['login'], user_info['image']['versions']['small'])
        
        token = get_tokens_for_user(CustomUser.objects.get(email=user_info['email']))
        return JsonResponse(token, status=200)
'''

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
        register42User(user_info['email'], user_info['login'], user_info['image']['versions']['small'])
    
    token = get_tokens_for_user(CustomUser.objects.get(email=user_info['email']))
    return JsonResponse(token, status=200)
