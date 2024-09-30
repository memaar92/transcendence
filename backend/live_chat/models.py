from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Message(models.Model):
    content = models.CharField(max_length=1000)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='received_messages', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now, blank=True)
    status = models.CharField(max_length=10, default='unread')
    
    def __str__(self):
        return f"{self.sender.displayname} to {self.receiver.displayname} at {self.timestamp}: {self.content}"


class Relationship(models.Model):
    user1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requests_sent', on_delete=models.CASCADE)
    user2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='friend_requests_received', on_delete=models.CASCADE)
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_requests', on_delete=models.CASCADE, null=True, blank=True)
    blocker = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='blocked_users', on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class RelationshipStatus(models.TextChoices):
        DEFAULT = 'DF', _('Default')
        PENDING = 'PD', _('Pending')
        BEFRIENDED = 'BF', _('Befriended')
        BLOCKED = 'BL', _('Blocked')

    status = models.CharField(max_length=2, choices=RelationshipStatus.choices, default=RelationshipStatus.DEFAULT)

    class Meta:
        unique_together = ('user1', 'user2')

    def clean(self):
        if self.status == self.RelationshipStatus.BLOCKED and not self.blocker:
            raise ValidationError("Blocker must be set when the status is 'BLOCKED'.")
        if self.status != self.RelationshipStatus.BLOCKED:
            self.blocker = None

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def update_status(self, new_status, blocker_id=None):
        self.status = new_status
        if new_status == self.RelationshipStatus.BLOCKED:
            if not blocker_id:
                raise ValidationError("Blocker must be provided when the status is 'BLOCKED'.")
            self.blocker_id = blocker_id
        else:
            self.blocker = None
        self.save()