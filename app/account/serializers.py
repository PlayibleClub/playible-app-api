from rest_framework import serializers, status, validators

from account import models
from core import utils

# Account and asset data serializers
class AccountSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    """Serializer for account objects"""
    class Meta:
        model = models.Account
        fields = ['id', 'username', 'wallet_addr', 'image_url']
        read_only_fields = ['id']

    def validate(self, data):
        data['username'] = data.get('username', data.get('wallet_addr'))
        utils.getTxInfo("421D2EB3DB407AF523F228C2EE0877E5FE66976EDD54EA06CB16A5852A8DE447")
        return data

    def save(self):
        account = models.Account(
            username = self.validated_data['username'],
            wallet_addr = self.validated_data['wallet_addr'],
            image_url = self.validated_data.get('image_url', ''),
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

class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for prelaumch email objects"""
    class Meta:
        model = models.Collection
        fields = ['id', 'athlete_id', 'name', 'symbol','contract_addr']
        read_only_fields = ('id',)

    def save(self):
        collection = models.Collection(
            athlete_id = self.validated_data['athlete_id'],
            name = self.validated_data['name'],
            symbol = self.validated_data['symbol'],
            contract_addr = self.validated_data['contract_addr'],
        )

        collection.save()

        return {
            'message': "Collection added.",
            'id': contract.pk
        }

class EmailSerializer(serializers.ModelSerializer):
    """Serializer for Email objects"""
    class Meta:
        model = models.PrelaunchEmail
        fields = ['id', 'email']
        read_only_fields = ('id',)

    def save(self):
        prelaunchEmail = models.PrelaunchEmail(
            email = self.validated_data['email'],
        )

        prelaunchEmail.save()

        return {
            'message': "Prelaunch Email added.",
            'id': prelaunchEmail.pk
        }