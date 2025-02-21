import uuid

from django.db import models
from django.contrib.auth.models import UserManager
from django.contrib.auth.models import AbstractUser


class CostumUserManger(UserManager):
    pass

class Profile(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    password = models.CharField(max_length=120)
    image = models.ImageField(upload_to='profile_pics')
    description = models.TextField(max_length=500)

    favorits = models.ManyToManyField("chat.Chat", related_name="favorited_by", blank=True)
    blacklist = models.ManyToManyField("self", symmetrical=False, related_name="blocked_by", blank=True)

    objects = CostumUserManger()

    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کابران"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.username


