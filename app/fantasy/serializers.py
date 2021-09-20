from rest_framework import serializers, status, validators

from core import models
from core import utils


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
    """
    # save positions data on AthletePositions
    for position_data in self.validated_data['positions']:
      position = models.AthletePositions(
        athlete = athlete
        position = position_data
      )
      position.save()
    """
    return {
      'message': "Athlete added.",
      'id': athlete.pk
    }


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


class TeamSerializer(serializers.Serializer):
  location = serializers.CharField(required=False, allow_null=True)
  nickname = serializers.CharField(required=False, allow_null=True)
  api_id = serializers.IntegerField(
    required=False, 
    allow_null=True
  )

  class Meta:
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


class ContractSerializer(serializers.ModelSerializer):
  """Serializer for contract objects"""
  class Meta:
    model = models.AssetContract
    fields = ['id', 'name', 'symbol','contract_addr']
    read_only_fields = ('id',)

  def save(self):
    contract = models.AssetContract(
      # athlete_id = self.validated_data['athlete_id'],
      name = self.validated_data['name'],
      symbol = self.validated_data['symbol'],
      contract_addr = self.validated_data['contract_addr'],
    )

    contract.save()

    return {
      'message': "Contract Asset added.",
      'id': contract.pk
    }


class AccountSerializer(serializers.ModelSerializer):
  """Serializer for account objects"""
  class Meta:
    model = models.Account
    fields = ['id', 'username', 'wallet_addr', 'image_url']
    read_only_fields = ('id',)

  def save(self):
    account = models.Account(
      username = self.validated_data['username'],
      wallet_addr = self.validated_data['wallet_addr'],
      image_url = self.validated_data['image_url'],
    )

    account.save()

    return {
      'message': "Account added.",
      'id': account.pk
    }

class AssetSerializer(serializers.ModelSerializer):
  """Serializer for account objects"""
  class Meta:
    model = models.Asset
    fields = ['id', 'name', 'owner', 'contract', 'image_url']
    read_only_fields = ('id',)

  def save(self):
    asset = models.Asset(
      name = self.validated_data['name'],
      owner = self.validated_data['owner'],
      contract = self.validated_data['contract'],
      image_url = self.validated_data['image_url'],
    )

    asset.save()

    return {
      'message': "Asset added.",
      'id': asset.pk
    }