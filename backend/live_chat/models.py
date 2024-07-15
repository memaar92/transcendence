from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    
    def __str__(self):
        return f"Chat between {[user.username for user in self.participants.all()]}"

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    content = models.CharField(max_length=1000)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, blank=True)
    
    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username} at {self.timestamp}: {self.content}"
