import uuid
import random
from cryptography.fernet import Fernet
from django.apps import apps
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings

MAX_LENGTH_DISPLAYNAME = 20

# Generate a Fernet key
crypto_key = Fernet(settings.SECRET_KEY)

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

def send_otp_email(recipient, otp):
    subject = 'Email Verification'
    html_message = render_to_string('email_template.html', {'code': otp })
    plain_message = strip_tags(html_message)
    from_email = "Wayne from Transcendence <transcendene.pongo@gmail.com>"
    to = recipient

    send_mail(subject, plain_message, from_email, [to], html_message=html_message, fail_silently=False)

def encrypt_totp_secret(totp_secret):
    if isinstance(totp_secret, str):
        totp_secret = totp_secret.encode('utf-8')
    encrypted_secret = crypto_key.encrypt(totp_secret)
    return encrypted_secret.decode('utf-8')

def decrypt_totp_secret(encrypted_secret):
    if isinstance(encrypted_secret, str):
        encrypted_secret = encrypted_secret.encode('utf-8')
    decrypted_secret = crypto_key.decrypt(encrypted_secret)
    return decrypted_secret.decode('utf-8')