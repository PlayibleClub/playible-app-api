# Generated by Django 3.2.11 on 2022-03-08 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fantasy', '0024_alter_gameathletestat_season'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='primary_color',
            field=models.CharField(blank=True, max_length=155, null=True),
        ),
        migrations.AddField(
            model_name='team',
            name='secondary_color',
            field=models.CharField(blank=True, max_length=155, null=True),
        ),
    ]