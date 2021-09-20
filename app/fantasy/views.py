from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

from core import models
from fantasy import requests
from fantasy import serializers

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
                  mixins.CreateModelMixin):
  """Base viewset for table attributes"""

  def perform_create(self, serializer): 
    """Create a new object"""
    if(serializer.is_valid()):
        content = serializer.save()
        return Response(content, status=status.HTTP_200_OK)
    else:
        content = serializer.errors
        return Response(content, status=status.HTTP_400_BAD_REQUEST)

class PositionViewSet(BaseViewSet):
  """Manage positions in the database"""
  queryset = models.Positions.objects.all()
  serializer_class = serializers.PositionSerializer

class AthleteViewSet(viewsets.ModelViewSet):
  """Manage athletes in the database"""
  queryset = models.Athlete.objects.all()
  serializer_class = serializers.AthleteSerializer

  def _params_to_ints(self, qs):
    """Convert a list of string IDs to a list of integres"""
    return [int(str_id) for str_id in qs.split(',')]

  def get_queryset(self):
    """Retrieve the athlete"""
    team = self.request.query_params.get('team')
    positions = self.request.query_params.get('positions')
    queryset = self.queryset
    
    if team:
      team_ids = self._params_to_ints(team)
      queryset = queryset.filter(team__id__in = team_ids)
    if positions:
      position_ids = self._params_to_ints(positions)
      queryset = queryset.filter(position__id__in = position_ids)

    return queryset

  def create(self, serializer): 
    """Create a new athlete"""
    if(serializer.is_valid()):
      content = serializer.save()
      return Response(content, status=status.HTTP_200_OK)
    else:
      content = serializer.errors
      return Response(content, status=status.HTTP_400_BAD_REQUEST)
    
