# Generated by Django 3.2.11 on 2022-02-14 07:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fantasy', '0015_alter_gameasset_asset'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gameasset',
            name='game_athlete',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset', to='fantasy.gameathlete'),
        ),
    ]