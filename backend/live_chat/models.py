from django.db import models
from django.utils import timezone

# Create your models here.
class Chat(models.Model):
    participants = models.ManyToManyField('auth.User', related_name='chats')
    def __str__(self):
        return self.participants.all()

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    content = models.CharField(max_length=1000)
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    timestamp = models.DateTimeField(default=timezone.now, blank=True)
    def __str__(self):
        return self.user + "at" + self.timestamp + "said: " + self.message
