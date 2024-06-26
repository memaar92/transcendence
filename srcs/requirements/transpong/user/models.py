from django.db import models

class User(models.Model):
    id = models.AutoField(primary_key=True)  # For an auto-incrementing int
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Name: {self.name} ID: {self.id}"
    
class Games(models.Model):
    id = models.AutoField(primary_key=True)
    home_id = models.ForeignKey(User, related_name='home_id', on_delete=models.SET_NULL, null=True)
    visitor_id = models.ForeignKey(User, related_name='visitor_id', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Game {self.id} Home: {self.home_id} Visitor: {self.visitor_id}"