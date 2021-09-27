from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

from drf_yasg.utils import swagger_auto_schema

from core import models
from fantasy import requests
from fantasy import serializers
from core import utils

class PositionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
  queryset = models.Position.objects.all()
  serializer_class = serializers.PositionSerializer
  """
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
  """



class TeamViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
  """Manage teams in the database"""
  queryset = models.Team.objects.all()
  serializer_class = serializers.TeamSerializer

  @swagger_auto_schema(operation_description="Retrieves all NBA team data and saves it into the database.")
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
  """Manage athletes in the database"""
  queryset = models.Athlete.objects.all()
  serializer_class = serializers.AthleteSerializer
  
  @swagger_auto_schema(
    operation_description= "Creates an athlete instance in the database with the data from stats perform. The input could either be the name of the athlete or its corresponding id from stats perform."
  )
  def create(self, request, *args, **kwargs):
    response = requests.get('participants/')
    athlete_data = utils.filter_participant_data(response['response'], request.data)
    serializer = serializers.AthleteAPISerializer(data=athlete_data)
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

  @swagger_auto_schema(operation_description="Updates an athlete instance to reflect stats perform data.")
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


class AthleteSeasonViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
  """Manage athlete season data in the database"""
  queryset = models.AthleteSeason.objects.all()
  serializer_class = serializers.AthleteSeasonAPISerializer
  permission_classes = [AllowAny]

  def create(self, request, *args, **kwargs):
    try:
      athlete = models.AthleteSeason.objects.get(athlete__pk = request.data.get('athlete'))
      serializer = self.get_serializer(athlete, data=request.data)
    except models.AthleteSeason.DoesNotExist:
      serializer = self.get_serializer(data=request.data)
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_200_OK)
    else:
      content = serializer.errors
      return Response(content, status=status.HTTP_400_BAD_REQUEST)

    """
    response = requests.get('stats/players/' + athlete.get('api_id'))
    team_data = utils.parse_athlete_season_data(response['response'])
    serializer = self.get_serializer(data=team_data, many=True)
    if(serializer.is_valid()):
      serializer.save()
      return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
      content = {
        "message": "Failed to fetch data from Stats Perform API",
        "response": response['response']
      }
      return Response(content, status=status.HTTP_400_BAD_REQUEST)
    """
