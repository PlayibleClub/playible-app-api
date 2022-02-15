from django.db import models
from core.models import BaseInfo
from account.models import Account, Asset

class Athlete(BaseInfo):
    first_name = models.CharField(max_length=155, blank=True)
    last_name = models.CharField(max_length=155, blank=True)
    api_id = models.IntegerField(unique=True, blank=True) #athlete id from sportsdata
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
    duration = models.IntegerField() #TODO: Decide the unit of measurement (seconds/minutes/hours/days)
    prize = models.DecimalField(max_digits=19, decimal_places=2)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class GameSchedule(BaseInfo):
    game = models.OneToOneField("Game", on_delete=models.CASCADE)
    datetime = models.DateTimeField()
    team1 = models.OneToOneField("Team", on_delete=models.CASCADE, related_name="GameSchedule_team1")
    team2 = models.OneToOneField("Team", on_delete=models.CASCADE, related_name="GameSchedule_team2")

    def __str__(self):
        return self.game.name + ' ' + self.datetime
    
    class Meta:
        ordering = ['-created_at', '-updated_at']


class GameTeam(BaseInfo):
    name = models.CharField(max_length=155)
    game = models.OneToOneField("Game", on_delete=models.CASCADE)
    account = models.OneToOneField(Account, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class GameAthlete(BaseInfo):
    game = models.OneToOneField("Game", on_delete=models.CASCADE)
    athlete = models.OneToOneField("Athlete", on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class GameAsset(BaseInfo):
    game_team = models.OneToOneField("GameTeam", on_delete=models.CASCADE)
    game_athlete = models.OneToOneField("GameAthlete", on_delete=models.CASCADE)
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

class GameAthleteStat(BaseInfo):
    game_athlete = models.OneToOneField("GameAthlete", on_delete=models.CASCADE)
    game_schedule = models.OneToOneField("GameSchedule", on_delete=models.CASCADE)
    fantasy_score = models.DecimalField(max_digits=19, decimal_places=2)
    
    class Meta:
        ordering = ['-created_at', '-updated_at']

