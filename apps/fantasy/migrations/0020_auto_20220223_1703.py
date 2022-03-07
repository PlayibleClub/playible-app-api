# Generated by Django 3.2.11 on 2022-02-23 09:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fantasy', '0019_game_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='gameathletestat',
            name='game_athlete',
        ),
        migrations.RemoveField(
            model_name='gameschedule',
            name='game',
        ),
        migrations.AddField(
            model_name='gameathletestat',
            name='athlete',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='fantasy.athlete'),
        ),
        migrations.AddField(
            model_name='gameathletestat',
            name='singles',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=19),
        ),
        migrations.AddField(
            model_name='gameschedule',
            name='game_api_id',
            field=models.IntegerField(blank=True, default=None, unique=True),
        ),
        migrations.AlterField(
            model_name='gameathletestat',
            name='game_schedule',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='fantasy.gameschedule'),
        ),
        migrations.AlterField(
            model_name='gameschedule',
            name='team1',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_team1', to='fantasy.team'),
        ),
        migrations.AlterField(
            model_name='gameschedule',
            name='team2',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='schedule_team2', to='fantasy.team'),
        ),
    ]