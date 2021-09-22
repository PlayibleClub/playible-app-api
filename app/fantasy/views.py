from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from core import models
from fantasy import requests
from fantasy import serializers
from core import utils


class TeamViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
  queryset = models.Team.objects.all()
  serializer_class = serializers.TeamSerializer

  def create(self, request, *args, **kwargs):
    response = requests.get('teams/')
    team_data = utils.parse_team_list_data(response['response'])
    serializer = self.get_serializer(data=team_data, many=True)
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
      content = serializer.errors
      return Response(content, status=status.HTTP_400_BAD_REQUEST)


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

  def update(self, request, *args, **kwargs):
    return Response(status=status.HTTP_403_FORBIDDEN)


class PositionViewSet(BaseViewSet):
  """Manage positions in the database"""
  queryset = models.Positions.objects.all()
  serializer_class = serializers.PositionSerializer

  def partial_update(self, request, *args, **kwargs):
    table_object = self.get_object()
    data = request.data

    table_object.name = data.get("name", table_object.name)
    table_object.abbreviation = data.get("abbreviation", table_object.abbreviation)

    table_object.save()
    serializer = serializers.PositionSerializer(table_object, data, partial=True)
    
    if(serializer.is_valid()):
        return Response(serializer.data, status.HTTP_200_OK)
    else:
        content = serializer.errors
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
  

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

  def create(self, serializer): 
    #Create a new athlete
    table_object.save()
    serializer = serializers.ContractSerializer(table_object, data, partial=True)
    
    if(serializer.is_valid()):
        return Response(serializer.data, status.HTTP_200_OK)
    else:
        content = serializer.errors
        return Response(content, status=status.HTTP_400_BAD_REQUEST)


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

class TeamViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
  queryset = models.Team.objects.all()
  serializer_class = serializers.TeamSerializer

  def create(self, request, *args, **kwargs):
    response = requests.get('teams/')
    team_data = utils.parse_team_list_data(response['response'])
    serializer = self.get_serializer(data=team_data, many=True)
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
      content = serializer.errors
      return Response(content, status=status.HTTP_400_BAD_REQUEST)

class AthleteViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
  queryset = models.Athlete.objects.all()
  serializer_class = serializers.AthleteSerializer

  def create(self, request, *args, **kwargs):
    response = requests.get('participants/')
    athlete_data = utils.filter_participant_data(response['response'], request.data)
    serializer = serializers.AthleteAPISerializer(data=athlete_data)
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  def partial_update(self, request, pk=None):
    athlete = self.get_object()
    response = requests.get('participants/')
    athlete_data = utils.filter_participant_data(response['response'], {'api_id': athlete.api_id, 'terra_id': request.data.get('terra_id')})
    serializer = serializers.AthleteAPISerializer(athlete, data=athlete_data, partial=True)
    
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
  @swagger_auto_schema(auto_schema=None)
  def update(self, request, *args, **kwargs):
    return Response(status=status.HTTP_403_FORBIDDEN)

