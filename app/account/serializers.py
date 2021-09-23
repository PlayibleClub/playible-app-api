from rest_framework import serializers, status, validators

from core import models
from core import utils

# Account and asset data serializers
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

class ContractSerializer(serializers.ModelSerializer):
  """Serializer for contract objects"""
  class Meta:
    model = models.AssetContract
    fields = ['id', 'athlete_id', 'name', 'symbol','contract_addr']
    read_only_fields = ('id',)

  def save(self):
    contract = models.AssetContract(
      athlete_id = self.validated_data['athlete_id'],
      name = self.validated_data['name'],
      symbol = self.validated_data['symbol'],
      contract_addr = self.validated_data['contract_addr'],
    )

    contract.save()

    return {
      'message': "Contract Asset added.",
      'id': contract.pk
    }