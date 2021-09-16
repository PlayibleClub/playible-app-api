from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

from core import models
from fantasy import requests
from fantasy import serializers

from core import utils

class TeamViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
  queryset = models.Team.objects.all()
  serializer_class = serializers.TeamSerializer

  def create(self, request, *args, **kwargs):
    response = requests.get('teams/')
    team_data = utils.parse_team_list_data(response['response'])
    serializer = self.get_serializer(data=team_data, many=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    #TODO: Process response from Stats perform

    #serializer = self.get_serializer(data=request.data)
    #serializer.is_valid(raise_exception=True)
    #self.perform_create(serializer)
    #headers = self.get_success_headers(serializer.data)
    #return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    return Response(serializer.data, status=status.HTTP_201_CREATED)