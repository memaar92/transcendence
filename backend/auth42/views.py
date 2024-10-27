from django.shortcuts import redirect
from usermanagement.models import CustomUser
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings
from utils.utils import random_filename, generateUsername, get_tokens_for_user
from backend.utils import get_secret
from utils.mixins import CookieCreationMixin
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes
import requests
import json

HOST = settings.BASE_IP

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


def register42User(email, picture_url):
    username = generateUsername()
    while CustomUser.objects.filter(displayname=username).exists():
        username = generateUsername()
    picture_name = getProfilePicture(picture_url)
    new_user = CustomUser(email=email, displayname=username, is_42_auth=True, profile_picture=picture_name)
    new_user.save()


class Redirect42Auth(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            (200, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['Successfully authenticated with 42']}
                },
            },
            (400, 'application/json'): {
                'type': 'object',
                'properties': {
                    'detail': {'type': 'string', 'enum': ['42auth failed', 'Wrong authentication method']}
                },
            },
        },
    )

    def get(self, request):
        global HOST
        if request.get_host() == 'localhost':
            HOST = 'localhost'
        elif request.get_host() == settings.BASE_IP:
            HOST = settings.BASE_IP
        target_url = 'https://api.intra.42.fr/oauth/authorize?client_id=' + get_secret('oauth_client_id') + '&redirect_uri=https%3A%2F%2F' + HOST + '%2Fapi%2F42auth&response_type=code'
        return redirect(target_url)


class AuthWith42View(APIView, CookieCreationMixin):
    permission_classes = [AllowAny]

    @extend_schema(
        exclude=True
    )

    def get(self, request):
        new_user = False

        if (code := request.GET.get('code')) is None:
            return Response({'detail': '42auth failed: no code provided'}, status=400)
        code = request.GET.get('code')
        oauth_response = requests.post('https://api.intra.42.fr/oauth/token', data={
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': get_secret('oauth_client_id'),
            'client_secret': get_secret('oauth_secret'),
            'redirect_uri': 'https://' + HOST + '/api/42auth'
        }).json()
        if (oauth_response.get('error')):
            #case: issue with 42 auth
            response = Response(status=302)
            response['Location'] = 'https://' + HOST + '/42auth_failed?error=42api'
            return response
        user_info = requests.get('https://api.intra.42.fr/v2/me', headers={
            'Authorization': 'Bearer ' + oauth_response['access_token']
        }).json()

        user = CustomUser.objects.filter(email=user_info['email']).values('email', 'is_42_auth', 'is_2fa_enabled')
        if user.exists() and user.first()['is_42_auth'] == False:
            # case: wrong auth method
            response = Response(status=302)
            response['Location'] = 'https://' + HOST + '/42auth_failed?error=42email'
            return response
        elif not user.exists():
            register42User(user_info['email'], user_info['image']['versions']['small'])
            new_user = True
        token = get_tokens_for_user(CustomUser.objects.get(email=user_info['email']))
        response = Response(token, status=302)
        if user.first()['is_2fa_enabled'] == True:
            response['Location'] = 'https://' + HOST + '/verify_2fa'
        elif new_user:
            response['Location'] = 'https://' + HOST + '/player_creation'
        else:
            response['Location'] = 'https://' + HOST + '/main_menu'
        self.createCookies(response)
        return response
