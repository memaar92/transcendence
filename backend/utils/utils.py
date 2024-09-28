import uuid
import random
import os
from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
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

def send_otp_email(recipient, otp):
    subject = 'Email Verification'
    html_message = render_to_string('email_template.html', {'code': otp })  # Ensure 'email_template.html' is in one of your template directories
    plain_message = strip_tags(html_message)
    from_email = 'transcendene.pongo@gmail.com'
    to = recipient

    send_mail(subject, plain_message, from_email, [to], html_message=html_message)
    