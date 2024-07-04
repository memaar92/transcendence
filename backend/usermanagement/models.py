from django.db import models

from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics', default='default.jpg')

    def __str__(self):
        return f'{self.user.username} Profile'
    
class Games(models.Model):
    id = models.AutoField(primary_key=True)
    home_id = models.ForeignKey(User, related_name='home_id', on_delete=models.SET_NULL, null=True)
    visitor_id = models.ForeignKey(User, related_name='visitor_id', on_delete=models.SET_NULL, null=True)
    visitor_score = models.IntegerField()
    home_score = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Game {self.id} Home: {self.home_id} Visitor: {self.visitor_id}"