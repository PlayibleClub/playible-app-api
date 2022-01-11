from rest_framework import serializers, status, validators

from fantasy import models
from core import utils

# Fantasy data serializers
class TeamListSerializer(serializers.ListSerializer):
  def save(self):
    teams_list = []
    for team_data in self.validated_data:
      team, is_created = models.Team.objects.get_or_create(
        api_id = team_data['api_id'],
        defaults = {
          'location': team_data['location'],
          'name': team_data['name'],
        }
      )
      teams_list.append({
        "is_created": is_created,
        "data": team
      })
    return {
      'message': "Teams added.",
      'data': teams_list
    }


class TeamSerializer(serializers.ModelSerializer):
  location = serializers.CharField(required=False, allow_null=True)
  name = serializers.CharField(required=False, allow_null=True)
  api_id = serializers.IntegerField(
    required=False, 
    allow_null=True
  )

  class Meta:
    model = models.Team
    fields = ['id', 'location', 'name', 'api_id']
    read_only_fields = ['id']
    list_serializer_class = TeamListSerializer


class PositionSerializer(serializers.ModelSerializer):
  name = serializers.CharField()
  abbreviation = serializers.CharField()

  class Meta:
    model = models.Position
    fields = ['id', 'name', 'abbreviation']
    read_only_fields = ['id']

  def save(self):
    position, is_created = models.Position.objects.get_or_create(
      name = self.validated_data['name'],
      abbreviation = self.validated_data['abbreviation'],
    )

    return {
      'message': "Position added.",
      'id': position.pk
    }

#Serializer for Stats Perform API data
class AthleteAPISerializer(serializers.ModelSerializer):
  #team = serializers.PrimaryKeyRelatedField(queryset=models.Team.objects.all())
  #positions = serializers.PrimaryKeyRelatedField(queryset=models.Position.objects.all(), many=True)
  positions = PositionSerializer(many=True)

  class Meta:
    model = models.Athlete
    fields = [
      'first_name',
      'last_name',
      'api_id',
      'team',
      'positions',
      'jersey',
      'is_active',
      'is_injured',
      'is_suspended'
    ]
    read_only_fields = [
      'is_active',
      'is_injured',
      'is_suspended'
    ]

  def validate(self, data):
    positions_id_list = []

    for position_data in data['positions']:
      position, is_created = models.Position.objects.get_or_create(
        name=position_data['name'], 
        abbreviation=position_data['abbreviation'],
      )

      positions_id_list.append(position)

    data['positions'] = positions_id_list

    return data
    
  def save(self):
    if self.instance is not None:
      athlete = self.instance
      team = models.Team.objects.get(api_id=self.validated_data.get('team').id)
      athlete.first_name = self.validated_data.get('first_name')
      athlete.last_name = self.validated_data.get('last_name')
      athlete.terra_id = self.validated_data.get('terra_id', self.instance.terra_id)
      athlete.api_id = self.validated_data.get('api_id')
      athlete.team = team
    else:
      athlete = models.Athlete(
        first_name = self.validated_data['first_name'],
        last_name = self.validated_data['last_name'],
        terra_id = self.validated_data['terra_id'],
        api_id = self.validated_data['api_id'],
        team = self.validated_data['team'],
      )
    athlete.save()
    athlete.positions.set(self.validated_data['positions'])

    return {
      'message': "Athlete added.",
      'id': athlete.pk
    }

class AthleteSerializer(serializers.ModelSerializer):
  api_id = serializers.IntegerField(
    required=False, 
    allow_null=True
  )
  team = TeamSerializer(read_only=True)
  positions = PositionSerializer(many=True, read_only=True)

  class Meta:
    model = models.Athlete
    fields = [
      'id',
      'first_name',
      'last_name',
      'terra_id',
      'api_id',
      'team',
      'positions',
      'jersey',
      'is_active',
      'is_injured',
      'is_suspended'
    ]
    read_only_fields = [
      'id',
      'team',
      'positions',
      'jersey',
      'is_active',
      'is_injured',
      'is_suspended'
    ]

#Used for API data retrieval
class AthleteSeasonAPISerializer(serializers.ModelSerializer):
  fantasy_score = serializers.SerializerMethodField()
  class Meta:
    model = models.AthleteSeason
    fields = [
      'id',
      'athlete',
      'season',
      'fantasy_score',
      'points',
      'rebounds',
      'assists',
      'blocks',
      'turnovers'
    ]
    read_only_fields = [
      'id',
      'fantasy_score',
    ]

  def get_fantasy_score(self, obj):
    stats_info_list = models.StatsInfo.objects.filter(is_active=True)
    fantasy_score = 0
    for stats_info in stats_info_list:
      try:
        fantasy_score = fantasy_score + getattr(obj, stats_info.key) * stats_info.multiplier
      except AttributeError:
        pass
    return fantasy_score


class AthleteSeasonSerializer(serializers.ModelSerializer):
  fantasy_score = serializers.SerializerMethodField()

  class Meta:
    model = models.AthleteSeason
    fields = [
      'id',
      'athlete',
      'season',
      'fantasy_score',
      'points',
      'rebounds',
      'assists',
      'blocks',
      'turnovers'
    ]
    read_only_fields = [
      'id',
      'season', #latest season by default
      'fantasy_score',
      'points',
      'rebounds',
      'assists',
      'blocks',
      'turnovers'
    ]

  def get_fantasy_score(self, obj):
    stats_info_list = models.StatsInfo.objects.filter(is_active=True)
    fantasy_score = 0
    for stats_info in stats_info_list:
      try:
        fantasy_score = fantasy_score + getattr(obj, stats_info.key) * stats_info.multiplier
      except AttributeError:
        pass
    return fantasy_score