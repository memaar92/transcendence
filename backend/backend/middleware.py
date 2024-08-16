from django.http import HttpResponse
import json
import redis
from django.conf import settings

# add checks for token validity?
class AuthorizationMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request):
        # print("request.META: ", request.META)
        access_token = request.COOKIES.get('access_token') #do the same for refresh token? --> this should be sent in the body of the request
        if access_token and not request.path == '/api/token/refresh/':
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'
        request_token = request.COOKIES.get('refresh_token')
        if request_token and request.path == '/api/token/refresh/':
            data = {'refresh': request_token}
            request._body = json.dumps(data).encode('utf-8')
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

        return response