import uuid
import random
import os
from django.apps import apps

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

