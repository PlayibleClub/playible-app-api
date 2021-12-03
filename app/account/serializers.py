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

class CollectionSerializer(serializers.ModelSerializer):
    """Serializer for collection objects"""
    contract_addr = serializers.CharField()
    contract_info = serializers.SerializerMethodField()

    class Meta:
        model = models.Collection
        fields = ['id', 'contract_addr', 'contract_info']
        read_only_fields = ['id', 'contract_info']

    def get_contract_info(self, obj):
        if self.instance is not None:
            contract_info = terra.query_contract(getattr(obj, "contract_addr"), { "contract_info":{}})
        else:
            contract_info = terra.query_contract(obj, { "contract_info":{}})
        return contract_info

    def validate(self, data):
        try:
            terra.query_contract(data["contract_addr"], { "contract_info":{}})
        except:
            raise serializers.ValidationError('Failed to query contract information from the provided contract address.')
        return data

    def save(self):
        if self.instance is not None:
            collection = self.instance
            collection.contract_addr = self.validated_data.get('contract_addr')
        else:
            collection = models.Collection(
                contract_addr = self.validated_data['contract_addr'],
            )
        collection.save()

        return {
            'message': "Collection added.",
            'id': collection.pk
        }

class AssetSerializer(serializers.ModelSerializer):
    """Serializer for account objects"""
    token_info = serializers.SerializerMethodField()
    collection = CollectionSerializer()
    owner = AccountSerializer(read_only=True)
    #contract_addr = serializers.CharField(write_only=True)

    class Meta:
        model = models.Asset
        fields = ['id', 'token_id', 'owner', 'collection', 'token_info']
        read_only_fields = ['id', 'token_info', 'collection', 'owner']

    def get_token_info(self, obj):
        if self.instance is not None:
            token_info = terra.query_contract(getattr(obj, "collection").contract_addr, { "nft_info":{ "token_id": getattr(obj, "token_id")}})
        else:
            token_info = terra.query_contract(obj["collection"].contract_addr, { "nft_info":{ "token_id": obj["token_id"]}})
        return token_info

    def validate(self, data):
        try:
            owner_info = terra.query_contract(data["collection"].get('contract_addr'), { "owner_of":{ "token_id": data["token_id"]}})
        except:
            raise serializers.ValidationError('Failed to query token information from the provided contract address with the provided token ID.')
        
        owner, is_created = models.Account.objects.get_or_create(
            wallet_addr=owner_info.get('owner')
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=data['collection'].get('contract_addr')
        )

        asset = models.Asset.objects.filter(
            token_id = data['token_id'],
            collection = collection
        )

        if asset.exists() and self.instance is None:
            raise serializers.ValidationError('The asset already exists in the database.')

        data['owner'] = owner
        data['collection'] = collection
        return data

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

class AccountAssetSerializer(serializers.Serializer):
    account = AccountSerializer(read_only=True)
    assets = AssetSerializer(read_only=True, many=True)

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
    collection = serializers.CharField(write_only=True)
    token_id = serializers.CharField(write_only=True)
    #asset = AssetSerializer(read_only=True)

    class Meta:
        model = models.SalesOrder
        fields = ['id', 'collection', 'token_id', 'asset', 'price', 'signed_message', 'message']
        read_only_fields = ['id', 'asset']

    def validate(self, data):
        
        try:
            owner_info = terra.query_contract(data["collection"], { "owner_of":{ "token_id": data["token_id"]}})
        except:
            raise serializers.ValidationError('Failed to query token information from the provided contract address with the provided token ID.')

        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=data['collection']
        )
        owner, is_created = models.Account.objects.get_or_create(
            wallet_addr=owner_info.get('owner')
        )
        asset, is_created = models.Asset.objects.get_or_create(
            token_id=data['token_id'],
            collection=collection,
            owner=owner
        )
        try:
            salesOrder = models.SalesOrder.objects.get(
                asset=asset
            )
            raise serializers.ValidationError('The asset has already been listed for sale.')
        except models.SalesOrder.DoesNotExist:
            pass

        data['asset'] = asset
        return data

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