# Generated by Django 3.2.7 on 2021-09-24 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_rename_positions_position'),
    ]

    operations = [
        migrations.AlterField(
            model_name='athleteseason',
            name='season',
            field=models.CharField(max_length=155),
        ),
        migrations.DeleteModel(
            name='Season',
        ),
    ]