from django.conf import settings

class CookieCreationMixin:
    def createCookies(self, response):
        response.set_cookie(
            key = settings.SIMPLE_JWT['AUTH_COOKIE'],
            value = response.data['access'],
            expires = settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        )
        response.set_cookie(
            key = settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH'],
            value = response.data['refresh'],
            path = settings.SIMPLE_JWT['AUTH_COOKIE_REFRESH_PATH'],
            expires = settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'],
            secure = settings.SIMPLE_JWT['AUTH_COOKIE_SECURE'],
            httponly = settings.SIMPLE_JWT['AUTH_COOKIE_HTTP_ONLY'],
            samesite = settings.SIMPLE_JWT['AUTH_COOKIE_SAMESITE'],
        )
        del response.data['access']
        del response.data['refresh']
