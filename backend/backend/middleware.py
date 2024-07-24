from django.http import HttpResponse

# add checks for token validity?

class AuthorizationMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response
    
    def __call__(self, request):
        print("request.META: ", request.META)
        token = request.COOKIES.get('access_token') #do the same for refresh token?
        if token:
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {token}'
        return self.get_response(request)