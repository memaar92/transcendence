import uuid
import random
import os
from django.apps import apps
from rest_framework_simplejwt.tokens import RefreshToken

MAX_LENGTH_DISPLAYNAME = 20

def random_filename(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"profile_pics/{filename}"

def randomDigits(digits):
    lower = 10**(digits-1)
    upper = 10**digits - 1
    return random.randint(lower, upper)

def generateUsername():
    config = apps.get_app_config('usermanagement')
    adjective = random.choice(config.adjectives)
    noun = random.choice(config.nouns)
    num = randomDigits(MAX_LENGTH_DISPLAYNAME - len(str(adjective)) - len(str(noun)))
    username = adjective + noun + str(num)
    return username

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['2fa'] = 0
    if user.is_2fa_enabled:
        refresh['2fa'] = 1
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }

def get_secret(secret_name):
    try:
        with open(f'/run/secrets/{secret_name}') as secret_file:
            return secret_file.read().strip()
    except IOError as e:
            raise Exception(f'Critical error reading secret {secret_name}: {e}')
