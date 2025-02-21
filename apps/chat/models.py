from django.db import models
from apps.account.models import Profile


class Chat(models.Model) :
    is_group = models.BooleanField(default=False, null=False, blank=False)
    create_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="created_chats")
    participants = models.ManyToManyField(Profile, related_name="chats")
    created = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'Chat  {self.name} '
    class Meta:
        verbose_name = "چت"
        verbose_name_plural = "چت ها"

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages", null=True)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE)
    message = models.TextField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.sender.username}: {self.message}'

    class Meta:
        verbose_name = "پیام"
        verbose_name_plural = "پیام ها"
