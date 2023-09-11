# Generated by Django 4.2.3 on 2023-09-10 09:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ban',
            name='chat_owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bans_of_chat', to=settings.AUTH_USER_MODEL, verbose_name='Chat Owner'),
        ),
    ]