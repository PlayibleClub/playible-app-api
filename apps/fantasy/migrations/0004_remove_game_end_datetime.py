# Generated by Django 3.2.11 on 2022-02-14 03:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('fantasy', '0003_alter_game_end_datetime'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='game',
            name='end_datetime',
        ),
    ]