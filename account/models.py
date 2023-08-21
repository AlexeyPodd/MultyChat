from django.contrib.auth.models import AbstractUser
from django.db import models
from django_extensions.db.fields import AutoSlugField


class User(AbstractUser):
    username_slug = AutoSlugField(populate_from='username', unique=True, verbose_name='Username Slug')
    email = models.EmailField(unique=True, verbose_name='Email')
    black_listed_users = models.ManyToManyField('self', blank=True, symmetrical=False,
                                                related_name='baned_in_user_chats', verbose_name='Blacklisted Users')
    moderators = models.ManyToManyField('self', blank=True, symmetrical=False,
                                        related_name='moderating_user_chats', verbose_name='User Chat Moderators')
    allowed_run_chat = models.BooleanField(default=True, verbose_name='User is allowed to run Chat')
    is_running_chat = models.BooleanField(default=False, verbose_name='User\'s Chat is running now')

    def __str__(self):
        return self.username
