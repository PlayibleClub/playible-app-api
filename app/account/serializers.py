from rest_framework import serializers, status, validators

from account import models
from core import utils
from core import terra

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
    token_info = serializers.SerializerMethodField()

    class Meta:
        model = models.Asset
        fields = ['id', 'token_id', 'owner', 'collection', 'token_info']
        read_only_fields = ['id']

    def get_token_info(self, obj):
        #token_info = terra.query_contract(getattr(obj, 'collection'), { "contract_info":{}})
        return getattr(obj, 'collection').contract_addr

    def save(self):
        asset = models.Asset(
            token_id = self.validated_data['token_id'],
            owner = self.validated_data['owner'],
            collection = self.validated_data['collection'],
        )

        asset.save()

        return {
            'message': "Asset added.",
            'id': asset.pk
        }

class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collection objects"""
    contract_info = serializers.SerializerMethodField()

    class Meta:
        model = models.Collection
        fields = ['id', 'admin_addr','contract_addr', 'contract_info']
        read_only_fields = ['id', 'contract_info']

    def get_contract_info(self, obj):
        contract_info = terra.query_contract(getattr(obj, 'contract_addr'), { "contract_info":{}})
        return contract_info

    def validate(self, data):
        return data

    def save(self):
        collection = models.Collection(
            admin_addr = self.validated_data['admin_addr'],
            contract_addr = self.validated_data['contract_addr'],
        )

        collection.save()

        return {
            'message': "Collection added.",
            'id': collection.pk
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

class SalesOrderSerializer(serializers.ModelSerializer):
    """Serializer for Sales Order objects"""
    class Meta:
        model = models.SalesOrder
        fields = ['id', 'asset', 'price', 'signed_message', 'message']
        read_only_fields = ('id',)

    def save(self):
        salesOrder = models.SalesOrder(
            asset = self.validated_data['asset'],
            price = self.validated_data['price'],
            signed_message = self.validated_data['signed_message'],
            message = self.validated_data['message'],
        )

        salesOrder.save()

        return {
            'message': "Sales Order added.",
            'id': salesOrder.pk
        }