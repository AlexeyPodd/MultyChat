from django.db import models

from multychats.settings import AUTH_USER_MODEL


class Ban(models.Model):
    banned_user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE,
                                    related_name='bans', verbose_name='Banned User')
    chat_owner = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   related_name='bans_of_chat', verbose_name='Chat Owner')
    time_start = models.DateTimeField(auto_now_add=True, verbose_name='Date of Ban')
    time_end = models.DateTimeField(blank=True, null=True, verbose_name='Date of Ban end')
    banned_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
                                  related_name='moder_bans', verbose_name='Banned by')

    class Meta:
        verbose_name = 'Ban'
        verbose_name_plural = 'Bans'
        ordering = ['time_start', 'chat_owner', 'banned_user']
