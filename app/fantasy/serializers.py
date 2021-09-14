from rest_framework import serializers, status

from core import models

class AthleteSerializer(serializers.ModelSerializer):
  class Meta:
    model = models.Athlete
    fields = [
      'name',
      'terra_id',
      'api_id',
    ]

  def validate(self, data):
    # request athlete data

    # validate input and requested data

    # match retrieved team with the saved teams in the database

    # process positions data with PositionSerializer

    return data
    
  def save(self):
    athlete = models.Athlete(
      name = self.validated_data['name'],
      terra_id = self.validated_data['terra_id'],
      api_id = self.validated_data['api_id'],
      team = self.validated_data['team'],
      jersey = self.validated_data['jersey'],
      is_active = self.validated_data['is_active'],
      is_injured = self.validated_data['is_injured'],
      is_suspended = self.validated_data['is_suspended'],
    )
    athlete.save()

    # save positions data on AthletePositions
    for position_data in self.validated_data['positions']:
      position = models.AthletePositions(
        athlete = athlete
        position = position_data
      )
      position.save()

    return {
      'message': "Athlete added.",
      'id': athlete.pk
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