from django.shortcuts import render
from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response

from core import models
from fantasy import requests
from fantasy import serializers

class TeamViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
  queryset = models.Team.objects.all()
  serializer_class = serializers.TeamSerializer

  def create(self, request, *args, **kwargs):
    response = requests.get('teams/')

    #TODO: Process response from Stats perform

    #serializer = self.get_serializer(data=request.data)
    #serializer.is_valid(raise_exception=True)
    #self.perform_create(serializer)
    #headers = self.get_success_headers(serializer.data)
    #return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    return Response(response, status=status.HTTP_201_CREATED)

class PositionViewSet(generics.GenericAPIView):
  serializer_class = serializers.PositionSerializer

  def post(self, request):
    serializer = serializers.PositionSerializer(data=request.data, context={'request':request})

    if(serializer.is_valid()):
        content = serializer.save()
        return Response(content, status=status.HTTP_200_OK)
    else:
        content = serializer.errors
        return Response(content, status=status.HTTP_400_BAD_REQUEST)
    
  def get(self):
    queryset = models.Positions.objects.all()
    serializer = serializers.PositionSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)