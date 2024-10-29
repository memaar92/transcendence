from django.contrib import admin
from .models import CustomUser, Games

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Games)
