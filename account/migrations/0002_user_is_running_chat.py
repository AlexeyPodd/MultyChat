# Generated by Django 4.2.3 on 2023-08-19 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_running_chat',
            field=models.BooleanField(default=False, verbose_name="User's Chat is running now"),
        ),
    ]