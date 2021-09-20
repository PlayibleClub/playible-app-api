# Generated by Django 3.2.7 on 2021-09-17 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_alter_team_api_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='athleteseason',
            name='fantasy_score',
            field=models.DecimalField(decimal_places=10, default=0, max_digits=19),
            preserve_default=False,
        ),
    ]