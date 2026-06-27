from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    discord_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=200, blank=True)
    reputation_score = models.IntegerField(default=0)

    def __str__(self):
        return self.display_name or self.username
