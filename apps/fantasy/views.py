from django.shortcuts import render
from django.conf import settings

from rest_framework import status, generics, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated


from drf_yasg.utils import swagger_auto_schema

from apps.fantasy.models import *
from apps.fantasy import requests
from apps.fantasy.serializers import *
from apps.core import utils

# TODO: Define permissions for create and update actions


class TeamViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Manage teams in the database"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(operation_description="Retrieves all NBA team data and saves it into the database.")
    def create(self, request, *args, **kwargs):
        response = requests.get('scores/json/teams')

        if response['status'] == settings.RESPONSE['STATUS_OK']:
            team_data = utils.parse_team_list_data(response['response'])
            serializer = self.get_serializer(data=team_data, many=True)

            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            content = {
                "message": "Failed to fetch data from Stats Perform API",
                "response": response['response']
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class AthleteAPIViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Manage athletes in the database"""
    queryset = Athlete.objects.all()
    serializer_class = BlankSerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Creates an athlete instance in the database with the data from stats perform. The input could either be the name of the athlete or its corresponding id from stats perform."
    )
    def create(self, request, *args, **kwargs):
        response = requests.get('scores/json/Players')

        if response['status'] == settings.RESPONSE['STATUS_OK']:
            athlete_data = utils.parse_athlete_list_data(response['response'])

            serializer = AthleteAPISerializer(
                data=athlete_data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            content = {
                "message": "Failed to fetch data from Stats Perform API",
                "response": response['response']
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # TODO: Partial update for athlete data


class AthleteViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Manage athletes in the database"""
    queryset = Athlete.objects.all()
    serializer_class = AthleteSerializer
    permission_classes = [AllowAny]


class GameViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Manage games in the database"""
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [AllowAny]

    action_serializers = {
        'create': GameCreateSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(GameViewSet, self).get_serializer_class()


class GameLeaderboardView(generics.GenericAPIView):
    """Manage athletes in the database"""
    queryset = Game.objects.all()
    serializer_class = GameLeaderboardSerializer
    permission_classes = [AllowAny]

    def get(self, request, pk=None):
        try:
            game = self.get_object()  # get game object
            # TODO: get the top 10 game accounts
            # hard coded data for now
            game_accounts = [
                {
                    "address": "sample address1",
                    "fantasy_score": 10,
                    "rank": 1
                },
                {
                    "address": "sample address2",
                    "fantasy_score": 5,
                    "rank": 2
                }
            ]
            serializer = self.get_serializer(
                data={
                    "prize": game.prize,
                    "winners": game_accounts
                }
            )
            serializer.is_valid(raise_exception=True)
            content = serializer.data
            return Response(content, status=status.HTTP_200_OK)
        except:
            return Response("An error has occured", status=status.HTTP_400_BAD_REQUEST)
