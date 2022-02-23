import datetime
from time import time

from django.db import models
from django.utils import timezone

from apps.core.models import BaseInfo
from apps.account.models import Account, Asset


class Athlete(BaseInfo):
    first_name = models.CharField(max_length=155, blank=True)
    last_name = models.CharField(max_length=155, blank=True)
    # athlete id from sportsdata
    api_id = models.IntegerField(unique=True, blank=True)
    team = models.ForeignKey("Team", on_delete=models.CASCADE, blank=True)
    position = models.CharField(max_length=2, blank=True, null=True)
    jersey = models.IntegerField(null=True, blank=True)
    salary = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True, blank=True)
    is_injured = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    class Meta:
        ordering = ['-created_at', '-updated_at']


class PackAddress(BaseInfo):
    release = models.CharField(max_length=155)
    open_pack_addr = models.CharField(max_length=155)
    token_addr = models.CharField(max_length=155)


class StatsInfo(BaseInfo):
    name = models.CharField(max_length=155)
    key = models.CharField(max_length=155, unique=True)
    multiplier = models.DecimalField(max_digits=19, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at', '-updated_at']


class Team(BaseInfo):
    location = models.CharField(max_length=155)
    name = models.CharField(max_length=155)
    api_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.location + ' ' + self.name

    class Meta:
        ordering = ['-created_at', '-updated_at']


class Game(BaseInfo):
    name = models.CharField(max_length=155)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField(blank=True, null=True, default=None)
    # TODO: Decide the unit of measurement (seconds/minutes/hours/days)
    duration = models.IntegerField()
    prize = models.DecimalField(max_digits=19, decimal_places=2)
    image = models.ImageField(upload_to='games', null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-updated_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.end_datetime = self.start_datetime + timezone.timedelta(minutes=int(self.duration))
        super(Game, self).save(*args, **kwargs)


class GameSchedule(BaseInfo):
    game_api_id = models.IntegerField(unique=True, blank=True, default=None)
    datetime = models.DateTimeField()
    team1 = models.ForeignKey(
        "Team", on_delete=models.CASCADE, related_name="schedule_team1")
    team2 = models.ForeignKey(
        "Team", on_delete=models.CASCADE, related_name="schedule_team2")

    def __str__(self):
        return str(self.game_api_id)

    class Meta:
        ordering = ['-created_at', '-updated_at']


class GameTeam(BaseInfo):
    name = models.CharField(max_length=155)
    game = models.ForeignKey("Game", on_delete=models.CASCADE, related_name="teams")
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    fantasy_score = models.DecimalField(max_digits=19, decimal_places=2, default=0)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at', '-updated_at']


class GameAthlete(BaseInfo):
    game = models.ForeignKey("Game", on_delete=models.CASCADE)
    athlete = models.ForeignKey("Athlete", on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at', '-updated_at']


class GameAsset(BaseInfo):
    game_team = models.ForeignKey("GameTeam", on_delete=models.CASCADE, related_name="assets")
    game_athlete = models.ForeignKey(
        "GameAthlete", on_delete=models.CASCADE, related_name="asset")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at', '-updated_at']


class GameAthleteStat(BaseInfo):
    game_schedule = models.ForeignKey("GameSchedule", on_delete=models.CASCADE, default=None)
    athlete = models.ForeignKey("Athlete", on_delete=models.CASCADE, default=None)
    fantasy_score = models.DecimalField(max_digits=19, decimal_places=2, default=0)
    singles = models.DecimalField(max_digits=19, decimal_places=2, default=0)

    class Meta:
        ordering = ['-created_at', '-updated_at']
