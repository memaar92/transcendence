from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class Message(models.Model):
    content = models.CharField(max_length=1000)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, blank=True)
    
    def __str__(self):
        return f"{self.sender.displayname} to {self.receiver.displayname} at {self.timestamp}: {self.content}"

class Relationship(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requests_sent', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requests_received', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class RelationshipStatus(models.TextChoices):
    
        DEFAULT = 'DF', _('Default')
        PENDING = 'PD', _('Pending')
        BEFRIENDED = 'BF', _('Befriended')
        BLOCKED = 'BL', _('Blocked')

    status = models.CharField(max_length=2, choices=RelationshipStatus.choices, default=RelationshipStatus.DEFAULT)

    class Meta:
        unique_together = ('user1', 'user2')