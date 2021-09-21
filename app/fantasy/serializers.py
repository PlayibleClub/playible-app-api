from rest_framework import serializers, status, validators

from core import models
from core import utils

"""
class PositionSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.Position
    fields = [
      'name',
      'abbreviation'
    ]
    
  def save(self):
    position = models.Position(
      name = self.validated_data['name'],
      abbreviation = self.validated_data['abbreviation'],
    )

    position.save()
    return {
      'message': "Position added.",
      'id': position.pk
    }

class PositionSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.Position
    fields = [
      'name',
      'abbreviation'
    ]
    
  def save(self):
    position = models.Position(
      name = self.validated_data['name'],
      abbreviation = self.validated_data['abbreviation'],
    )

    position.save()
    return {
      'message': "Position added.",
      'id': position.pk
    }
"""

class TeamListSerializer(serializers.ListSerializer):
  def save(self):
    teams_list = []
    for team_data in self.validated_data:
      team, is_created = models.Team.objects.get_or_create(
        api_id = team_data['api_id'],
        defaults = {
          'location': team_data['location'],
          'nickname': team_data['nickname'],
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
  nickname = serializers.CharField(required=False, allow_null=True)
  api_id = serializers.IntegerField(
    required=False, 
    allow_null=True
  )

  class Meta:
    model = models.Team
    fields = ['id', 'location', 'nickname', 'api_id']
    read_only_fields = ['id']
    list_serializer_class = TeamListSerializer

class PositionSerializer(serializers.ModelSerializer):
  """Serializer for position objects"""
  class Meta:
    model = models.Positions
    fields = ['id', 'name', 'abbreviation']
    read_only_fields = ('id',)

  def save(self):
    position = models.Positions(
      name = self.validated_data['name'],
      abbreviation = self.validated_data['abbreviation'],
    )

    position.save()

    return {
      'message': "Position added.",
      'id': position.pk
    }
    
class AthleteSerializer(serializers.ModelSerializer):
  team = serializers.PrimaryKeyRelatedField(queryset=models.Team.objects.all())
  positions = serializers.PrimaryKeyRelatedField(queryset=models.Positions.objects.all(), many=True)

  class Meta:
    model = models.Athlete
    fields = [
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
      'is_active',
      'is_injured',
      'is_suspended'
    ]
    
  def save(self):
    athlete = models.Athlete(
      first_name = self.validated_data['first_name'],
      last_name = self.validated_data['last_name'],
      terra_id = self.validated_data['terra_id'],
      api_id = self.validated_data['api_id'],
      jersey = self.validated_data['jersey'],
      team = self.validated_data['team'],
    )
    athlete.save()
    athlete.positions.set(self.validated_data['positions'])
    
    return {
      'message': "Athlete added.",
      'id': athlete.pk
    }
