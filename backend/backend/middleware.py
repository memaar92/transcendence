from django.http import HttpResponse

# EXCLUDE_FROM_MIDDLEWARE = set('Django_Rest_Framework.views.apiIndexView',
#                             'Django_Rest_Framework.views.IndexView',
#                              'accounts.views.RegisterView',
#                              'accounts.views.LoginView'
#                             )

EXCLUDE_FROM_MIDDLEWARE = ['Django_Rest_Framework.views.apiIndexView',
                            'Django_Rest_Framework.views.IndexView',
                            'usermanagement.views.CustomTokenObtainPairView',
                            'usermanagement.views.RegisterView'
]


class AuthorizationMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def process_view(self, request, view_func, view_args, view_kwargs):
        view_name = '.'.join((view_func.__module__, view_func.__name__))
        print(view_name)
        if view_name in EXCLUDE_FROM_MIDDLEWARE:
            return None
    
    def __call__(self, request):
        print("request", request.headers)
        token = request.COOKIES.get('access_token') #do the same for refresh token?
        if token:
            print("token", token)
            request.META['HTTP_AUTHORIZATION'] = f'Token {token}'
            print("request", request.headers)
        return self.get_response(request)