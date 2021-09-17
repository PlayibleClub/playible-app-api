from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

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
      