from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from account import models
from account import serializers
from core import utils
from core import terra

#TODO: Define permissions for create and update actions

class BaseViewSet(viewsets.GenericViewSet, 
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin
):
  """Base viewset for table attributes"""

  def perform_create(self, serializer): 
    """Create a new object"""
    if(serializer.is_valid()):
        content = serializer.save()
        return Response(content, status=status.HTTP_201_CREATED)
    else:
        content = serializer.errors
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
  
  def retrieve(self, request, *args, **kwargs):
    return super().retrieve(request, *args, **kwargs)

  @swagger_auto_schema(auto_schema=None)
  def update(self, request, *args, **kwargs):
    return Response(status=status.HTTP_403_FORBIDDEN)

class CollectionViewSet(BaseViewSet):
    """Manage collections in the database"""
    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer
    permission_classes = [AllowAny]
    '''
    def create(self, request, *args, **kwargs):
        try:
            collection = models.Collection.objects.get(collection__pk = request.data.get('collection'))
            serializer = self.get_serializer(collection, data=request.data)
        except models.Collection.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
        if(serializer.is_valid()):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            content = serializer.errors
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    '''

class AccountViewset(BaseViewSet):
    """Manage accounts in the database"""
    queryset = models.Account.objects.all()
    serializer_class = serializers.AccountSerializer
    permission_classes = [AllowAny]

    def partial_update(self, request, *args, **kwargs):
        table_object = self.get_object()
        data = request.data
    
        table_object.username = data.get("username", table_object.username)
        table_object.wallet_addr = data.get("wallet_addr", table_object.wallet_addr)
        table_object.image_url = data.get("image_url", table_object.image_url)

        table_object.save()
        serializer = serializers.AccountSerializer(table_object, data, partial=True)
        
        if(serializer.is_valid()):
            return Response(serializer.data, status.HTTP_200_OK)
        else:
            content = serializer.errors
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class AssetViewset(viewsets.GenericViewSet, 
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin):
    """Manage assets in the database"""
    queryset = models.Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    permission_classes = [AllowAny]



    '''
    def partial_update(self, request, *args, **kwargs):
        table_object = self.get_object()
        data = request.data

        try:
            owner = models.Account.objects.get(id=data["id"])
            table_object.owner = owner
        except KeyError:
            pass

        try:
            collection = models.Collection.objects.get(id=data["id"])
            table_object.collection = collection
        except KeyError:
            pass
    
        table_object.name = data.get("name", table_object.name)
        table_object.image_url = data.get("image_url", table_object.image_url)

        table_object.save()
        serializer = serializers.AssetSerializer(table_object, data, partial=True)
        
        if(serializer.is_valid()):
            return Response(serializer.data, status.HTTP_200_OK)
        else:
            content = serializer.errors
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    '''

class AccountAssetView(generics.GenericAPIView):
    queryset = models.Asset.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.AssetSerializer

    def get(self, request, wallet=None, contract=None):
        account, is_created = models.Account.objects.get_or_create(
            wallet_addr=wallet
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=contract
        )

        response = terra.query_contract(contract, { "tokens": { "owner": wallet }})
        assets = models.Asset.objects.none()
        for token in response['tokens']:
            asset, is_created = models.Asset.objects.get_or_create(
                token_id = token,
                owner = account,
                collection = collection,
            )
            assets = assets.union(models.Asset.objects.filter(pk=asset.pk))
        serializer = self.serializer_class(assets, many=True)
        #user = User.objects.get(username=request.user)
        #queryset = models.UserAddress.objects.filter(user=user)
        #serializer = serializers.UserAddressSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class EmailViewset(viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin
):
    """Manage prelaunch emails in the database"""
    queryset = models.PrelaunchEmail.objects.all()
    serializer_class = serializers.EmailSerializer

    def get_permissions(self):
        """Set custom permissions for each action."""
        if self.action in ['list']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['create']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer): 
        """Create a new prelaunch email"""
        if(serializer.is_valid()):
            content = serializer.save()
            return Response(content, status=status.HTTP_201_CREATED)
        else:
            content = serializer.errors
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

class SalesOrderViewset(BaseViewSet):
    """Manage sales order in the database"""
    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer
    permission_classes = [AllowAny]