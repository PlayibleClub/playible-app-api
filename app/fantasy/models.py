from django.db import models
from core.models import BaseInfo


class Position(BaseInfo):
  name = models.CharField(max_length=155)
  abbreviation = models.CharField(max_length=2)
  
  def __str__(self):
    return self.name
  
  class Meta:
    ordering = ['-created_at', '-updated_at']
    constraints = [
        models.UniqueConstraint(fields=['name','abbreviation'], name='unique_abbreviation'),
    ]


class Athlete(BaseInfo):
  first_name = models.CharField(max_length=155, blank=True)
  last_name = models.CharField(max_length=155, blank=True)
  api_id = models.IntegerField(unique=True, blank=True) #athlete id from sportsdata
  team = models.ForeignKey("Team", on_delete=models.CASCADE, blank=True)
  position = models.CharField(max_length=2, blank=True)
  jersey = models.IntegerField(null=True, blank=True)
  salary = models.IntegerField(null=True, blank=True)
  is_active = models.BooleanField(default=True, blank=True)
  is_injured = models.BooleanField(default=False, blank=True)

  def __str__(self):
      return self.first_name + ' ' + self.last_name
  
  class Meta:
      ordering = ['-created_at', '-updated_at']


class AthleteSeason(BaseInfo):
  athlete = models.OneToOneField("Athlete", on_delete=models.CASCADE)
  season = models.CharField(max_length=155)
  points = models.DecimalField(max_digits=19, decimal_places=0)
  rebounds = models.DecimalField(max_digits=19, decimal_places=0)
  assists = models.DecimalField(max_digits=19, decimal_places=0)
  blocks = models.DecimalField(max_digits=19, decimal_places=0)
  turnovers = models.DecimalField(max_digits=19, decimal_places=0)
  
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