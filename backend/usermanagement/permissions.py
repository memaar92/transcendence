#custom permission class

from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
import jwt
from django.conf import settings

class IsSelf(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class Check2FA(permissions.BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                # Extract the token part from the header
                token = auth_header.split(' ')[1]
                # Decode the token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                # Check if '2fa' in payload is None or True
                print("Is2fa")
                print(payload.get('2fa'))
                if payload.get('2fa') in [0, 2]:
                    return True
            except jwt.ExpiredSignatureError:
                return False
            except jwt.InvalidTokenError:
                return False
        raise PermissionDenied({'message': '2FA verification needed.'})
