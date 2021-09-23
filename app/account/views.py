from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from core import models
from account import serializers
from core import utils

class BaseViewSet(viewsets.GenericViewSet, 
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,):
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

class ContractViewSet(BaseViewSet):
  """Manage contracts in the database"""
  queryset = models.AssetContract.objects.all()
  serializer_class = serializers.ContractSerializer

  def partial_update(self, request, *args, **kwargs):
    table_object = self.get_object()
    data = request.data

    try:
      athlete_id = models.Athlete.objects.get(id=data["id"])
      table_object.athlete_id = athlete_id
    except KeyError:
      pass
 
    table_object.name = data.get("name", table_object.name)
    table_object.symbol = data.get("symbol", table_object.symbol)
    table_object.contract_addr = data.get("contract_addr", table_object.contract_addr)
    table_object.save()

class AccountViewset(BaseViewSet):
  """Manage accounts in the database"""
  queryset = models.Account.objects.all()
  serializer_class = serializers.AccountSerializer

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


class AssetViewset(BaseViewSet):
  """Manage assets in the database"""
  queryset = models.Asset.objects.all()
  serializer_class = serializers.AssetSerializer

  def partial_update(self, request, *args, **kwargs):
    table_object = self.get_object()
    data = request.data

    try:
      owner = models.Account.objects.get(id=data["id"])
      table_object.owner = owner
    except KeyError:
      pass

    try:
      contract = models.AssetContract.objects.get(id=data["id"])
      table_object.contract = contract
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
