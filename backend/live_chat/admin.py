from django.contrib import admin
from .models import Message, Relationship

# Register your models here.

admin.site.register(Relationship)
admin.site.register(Message)
