from django.http import HttpResponse
import json
import redis
from django.conf import settings

# add checks for token validity?
class AuthorizationMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request):
        access_token = request.COOKIES.get('access_token')
        if access_token and not request.path == '/api/token/refresh/':
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token and (request.path == '/api/token/refresh/'):
            temp = request.POST.copy()
            temp['refresh'] = refresh_token
            request.POST = temp
        return self.get_response(request)
    
redis_instance = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

class UserStateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Example of updating user state in Redis
        if request.user.is_authenticated:
            redis_instance.set(f"user:{request.user.id}:state", "online", ex=3600)  # 1 hour expiration

        response = self.get_response(request)
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            print("Request Content:", content)
        return response