import decimal
import xml.etree.ElementTree as ET
import xmltodict
import dicttoxml

from cgitb import lookup
from django.shortcuts import render
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.core.files import File

from rest_framework import status, generics, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated


from drf_yasg.utils import swagger_auto_schema

from apps.fantasy.models import *
from apps.fantasy import requests
from apps.fantasy.serializers import *
from apps.core import utils
from apps.core.utils import paginate

from config.settings.base import ROOT_DIR

# TODO: Define permissions for create and update actions


class TeamViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Manage teams in the database"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [AllowAny]

    # @swagger_auto_schema(operation_description="Retrieves all NBA team data and saves it into the database.")
    # def create(self, request, *args, **kwargs):
    #     response = requests.get('scores/json/teams')

    #     if response['status'] == settings.RESPONSE['STATUS_OK']:
    #         team_data = utils.parse_team_list_data(response['response'])
    #         serializer = self.get_serializer(data=team_data, many=True)

    #         if serializer.is_valid():
    #             serializer.save()
    #             return Response(serializer.data, status=status.HTTP_201_CREATED)
    #         else:
    #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     else:
    #         content = {
    #             "message": "Failed to fetch data from Stats Perform API",
    #             "response": response['response']
    #         }
    #         return Response(content, status=status.HTTP_400_BAD_REQUEST)


class GameScheduleView(generics.GenericAPIView):
    """Retrieves game schedule for the current year and saves it in database"""
    queryset = Game.objects.all()
    serializer_class = GameLeaderboardSerializer
    permission_classes = [AllowAny]

    def post(self, request, pk=None):
        now = timezone.now()
        season = now.strftime('%Y').upper()
        response = requests.get('scores/json/Games/' + season)

        if response['status'] == settings.RESPONSE['STATUS_OK']:
            data = response['response']

            game_schedules = []

            for schedule in data:
                team1 = None
                team2 = None

                try:
                    team1 = Team.objects.get(api_id=schedule.get('AwayTeamID'))
                    team2 = Team.objects.get(api_id=schedule.get('HomeTeamID'))
                except Team.DoesNotExist:
                    pass

                game_schedule = GameSchedule(
                    game_api_id=schedule.get('GameID'),
                    datetime=schedule.get('Day'),
                    team1=team1,
                    team2=team2
                )

                game_schedules.append(game_schedule)

            GameSchedule.objects.bulk_create(game_schedules)

            return Response(status=status.HTTP_201_CREATED)
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

            for athlete in athlete_data:
                team = Team.objects.get(api_id=athlete['team_id'])

                if athlete['is_active'] == 'Active':
                    athlete['is_active'] = True
                else:
                    athlete['is_active'] = False

                if athlete['is_injured'] is None:
                    athlete['is_injured'] = False
                else:
                    athlete['is_injured'] = True

                Athlete.objects.update_or_create(
                    api_id=athlete['api_id'],
                    defaults={
                        'first_name': athlete['first_name'],
                        'last_name': athlete['last_name'],
                        'position': athlete['position'],
                        'salary': athlete['salary'],
                        'jersey': athlete['jersey'],
                        'is_active': athlete['is_active'],
                        'is_injured': athlete['is_injured'],
                        'team': team
                    }
                )

            return Response(athlete_data)

            # return Response(athlete_data)

            # serializer = AthleteAPISerializer(
            #     data=athlete_data, many=True)
            # if serializer.is_valid():
            #     serializer.save()
            #     return Response(serializer.data, status=status.HTTP_201_CREATED)
            # else:
            #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            content = {
                "message": "Failed to fetch data from Stats Perform API",
                "response": response['response']
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

    # TODO: Partial update for athlete data


class AthleteViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Manage athletes in the database"""
    queryset = Athlete.objects.all().order_by('pk')
    serializer_class = AthleteSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    action_serializers = {
        'top_performers': AthleteStatDetailSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(AthleteViewSet, self).get_serializer_class()

    @paginate
    @action(detail=False)
    def top_performers(self, request):
        now = timezone.now()
        season = now.strftime('%Y').upper()
        # season = '2021'

        athlete_stats = GameAthleteStat.objects.filter(Q(season=season)).order_by('-fantasy_score')

        return athlete_stats

    @ action(detail=True)
    def stats(self, request, id=None):
        now = timezone.now()
        season = now.strftime('%Y').upper()
        # season = '2021'

        athlete = self.get_object()
        athlete_stat = GameAthleteStat.objects.filter(Q(season=season) & Q(athlete=athlete)).first()
        serialized_athlete_stat = AthleteStatDetailSerializer(athlete_stat).data

        if athlete_stat is None:
            serialized_athlete_stat['athlete'] = AthleteGameStatDetailSerializer(athlete).data

        return Response({"athlete_stat": serialized_athlete_stat})


class GameViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Manage games in the database"""
    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    action_serializers = {
        'create': GameCreateSerializer,
        'update': GameCreateSerializer,
        'test_update_scores': None,
        'leaderboard': GameTeamLeaderboardSerializer,
        'registered_teams': GameTeamListDetailSerializer,
        'active': GameSerializer
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(GameViewSet, self).get_serializer_class()

    @ paginate
    @ action(detail=True)
    def leaderboard(self, request, id=None):
        game = self.get_object()
        game_teams = game.teams.order_by('-fantasy_score')
        game_teams_arr = []

        for game_team in game_teams:
            game_teams_arr.append(game_team)

        if len(game_teams) < 10:
            n = 10 - len(game_teams)

            for i in range(n):
                game_teams_arr.append({
                    'name': 'Admin',
                    'fantasy_score': 0,
                    'account': {
                        'wallet_addr': 'terra1jrg2hv92xpjl4wwgd84jcm4cs2pfmzdxl6y2sx'
                    }
                })

        return game_teams_arr

    @ paginate
    @ action(detail=False)
    def new(self, request):
        now = timezone.now()
        games = Game.objects.filter(Q(start_datetime__gt=now))
        return games

    @ paginate
    @ action(detail=False)
    def completed(self, request):
        now = timezone.now()
        games = Game.objects.filter(Q(end_datetime__lt=now))
        return games

    @ paginate
    @ action(detail=False)
    def active(self, request):
        now = timezone.now()
        games = Game.objects.filter(Q(start_datetime__lte=now) & Q(end_datetime__gt=now))
        return games

    @ paginate
    @ action(detail=True)
    def registered_teams(self, request, id=None):
        game = self.get_object()
        wallet_addr = self.request.query_params.get('wallet_addr', None)
        teams = GameTeam.objects.none()

        if wallet_addr is not None:
            account = Account.objects.filter(Q(wallet_addr=wallet_addr)).first()

            if account:
                teams = GameTeam.objects.filter(Q(account=account) & Q(game=game))

        return teams

    @ action(detail=True)
    def registered_teams_detail(self, request, id=None):
        game = self.get_object()
        wallet_addr = self.request.query_params.get('wallet_addr', None)
        teams = GameTeam.objects.none()
        teams_data = []

        if wallet_addr is not None:
            account = Account.objects.filter(Q(wallet_addr=wallet_addr)).first()

            if account:
                teams = GameTeam.objects.filter(Q(account=account) & Q(game=game)).order_by('pk')

                for team in teams:
                    assets = team.assets.all()

                    athletes = []

                    data = {
                        'id': team.id,
                        'name': team.name,
                        'fantasy_score': team.fantasy_score,
                    }

                    for asset in assets:
                        athlete = asset.game_athlete.athlete

                        now = timezone.now()
                        season = now.strftime('%Y').upper()

                        athlete_stat = GameAthleteStat.objects.filter(Q(athlete=athlete) & Q(season=season)).first()
                        fantasy_score = 0

                        if athlete_stat:
                            fantasy_score = athlete_stat.fantasy_score

                        athlete_obj = {
                            'id': athlete.id,
                            'first_name': athlete.first_name,
                            'last_name': athlete.last_name,
                            'fantasy_score': fantasy_score
                        }

                        if athlete.nft_image:
                            athlete_obj['nft_image'] = athlete.nft_image.url

                        athletes.append(athlete_obj)

                    data['athletes'] = athletes
                    teams_data.append(data)

        return Response(teams_data)

    @ action(detail=False, methods=['post'])
    def test_update_scores(self, request):
        now = timezone.now()

        date_query = now.strftime('%Y-%b-%d').upper()
        # url = 'stats/json/PlayerGameStatsByDate/' + date_query
        url = 'stats/json/PlayerGameStatsByDate/' + '2017-SEP-01'

        response = requests.get(url)

        if response['status'] == settings.RESPONSE['STATUS_OK']:
            athlete_data = utils.parse_athlete_stat_data(response['response'])

            games = Game.objects.filter(Q(start_datetime__lte=now) & Q(end_datetime__gte=now))

            for game in games:
                game_teams = game.teams.all()

                for game_team in game_teams:
                    total_fantasy_score = 0
                    game_assets = game_team.assets.all()

                    for game_asset in game_assets:
                        athlete = game_asset.game_athlete.athlete

                        if athlete:
                            # Search athlete api id if it exists in today's game athletes
                            data = next((item for item in athlete_data if item["api_id"] == athlete.api_id), None)

                            if data:
                                total_fantasy_score += data['fantasy_score']

                    game_team.fantasy_score += decimal.Decimal(total_fantasy_score)
                    # game_team.save()

                GameTeam.objects.bulk_update(game_teams, ['fantasy_score'])

            return Response(athlete_data)
        else:
            content = {
                "message": "Failed to fetch data from Stats Perform API",
                "response": response['response']
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class GameTeamViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """Manage game teams in the database"""
    queryset = GameTeam.objects.all()
    serializer_class = GameTeamCreateSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    action_serializers = {
        'create': GameTeamCreateSerializer,
        'update': GameTeamUpdateSerializer
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(GameTeamViewSet, self).get_serializer_class()

    def create(self, request):
        """
        Create game team request
        """
        serializer = GameTeamCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_201_CREATED)

    def retrieve(self, request, id=None):
        team = self.get_object()
        assets = team.assets.all()

        athletes = []

        data = {
            'name': team.name,
            'fantasy_score': team.fantasy_score,
        }

        for asset in assets:
            athlete = asset.game_athlete.athlete

            now = timezone.now()
            season = now.strftime('%Y').upper()

            athlete_stat = GameAthleteStat.objects.filter(Q(athlete=athlete) & Q(season=season)).first()
            fantasy_score = 0

            if athlete_stat:
                fantasy_score = athlete_stat.fantasy_score

            athlete_obj = {
                'id': athlete.id,
                'first_name': athlete.first_name,
                'last_name': athlete.last_name,
                'fantasy_score': fantasy_score
            }

            if athlete.nft_image:
                athlete_obj['nft_image'] = athlete.nft_image.url

            athletes.append(athlete_obj)

        data['athletes'] = athletes

        return Response(data)


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


class PackAddressViewSet(viewsets.ModelViewSet):
    """
    Pack Adddress API
    """
    serializer_class = PackAddressDetailSerializer
    queryset = PackAddress.objects.all()
    permission_classes = [AllowAny]
