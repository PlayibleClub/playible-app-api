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

    @action(detail=False)
    def generate_athlete_images(self, request):
        output_dir = 'athlete_images/'
        file_extension = '.svg'

        athletes = Athlete.objects.filter(Q(jersey__isnull=False) & Q(position__isnull=False))

        for athlete in athletes:
            athlete_id = str(athlete.id)

            file_name = output_dir + athlete_id + file_extension

            f = open(file_name, 'w')
            svg = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 132 175"><defs><linearGradient id="bd75224a-1111-4a62-b75f-68bdb9efa51c" x1="-0.37" y1="-3.76" x2="139.96" y2="165.8" gradientTransform="translate(0 4)" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#7e7e7e"/><stop offset="1" stop-color="#a4a4a4"/></linearGradient><linearGradient id="b7badc8c-9365-401a-be37-aa1e2e693758" x1="66.06" y1="99.55" x2="132" y2="99.55" gradientUnits="userSpaceOnUse"><stop offset="0"/><stop offset="0.19" stop-color="#0a0a0a"/><stop offset="0.5" stop-color="#252525"/><stop offset="0.91" stop-color="#505151"/><stop offset="1" stop-color="#5a5c5c"/></linearGradient><linearGradient id="abf16437-76e4-4299-a12c-bb71e5b98d20" x1="9.14" y1="139.36" x2="122.67" y2="25.83" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#171718"/><stop offset="1" stop-color="#373839"/></linearGradient><linearGradient id="ad6c68c2-a413-4601-93d3-c164432a4344" x1="58.34" y1="81.63" x2="115.79" y2="24.19" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#171718" stop-opacity="0"/><stop offset="0.21" stop-color="#1e1e1f" stop-opacity="0.02"/><stop offset="0.43" stop-color="#333334" stop-opacity="0.1"/><stop offset="0.65" stop-color="#575757" stop-opacity="0.22"/><stop offset="0.88" stop-color="#888" stop-opacity="0.39"/><stop offset="1" stop-color="#a9a9a8" stop-opacity="0.5"/></linearGradient></defs><title>Los Angeles Angels - Mike Trout</title><g id="ac97e034-076e-46ff-93cb-64ee1c0e5aef" data-name="Shield BG"><path d="M0,24.1,66.1,0,132,24.1v98c0,23.4-17.5,35.4-26.2,38.5L66.1,175c-5.2-1.9-20.6-7.6-40.7-15.2S.1,131.5,0,122.1v-98Z" transform="translate(0 0)" style="fill:url(#bd75224a-1111-4a62-b75f-68bdb9efa51c)"/><path d="M66.1,0V6.88l61.14,22.26,4.76-5Z" transform="translate(0 0)" style="fill:#434343"/><path d="M0,24.1l4.66,4.55L66.1,6.88V0Z" transform="translate(0 0)" style="fill:#232323"/><path d="M66.06,168V175l39.74-14.4s26.2-9.28,26.2-38.5v-98l-4.76,5-.61,89c-6.31,24.69-16.35,33-23.19,36.25-1.61.77-6.37,2.49-15.81,5.9C78.55,163.57,71.08,166.2,66.06,168Z" transform="translate(0 0)" style="fill:url(#b7badc8c-9365-401a-be37-aa1e2e693758)"/><path d="M0,24.1l4.7,4.59q30.71,70,61.39,140.07V175l-39.9-14.86S0,151.46,0,122.1Z" transform="translate(0 0)" style="fill:#333"/><path d="M5.41,29.18,66.12,7.24,126.5,29.66v88.6s1.35,27.22-23.14,36.17S66.05,168,66.05,168L29.62,155S5.41,146.36,5.41,121.73Z" transform="translate(0 0)" style="stroke:#1b1b1b;stroke-miterlimit:10;stroke-width:1.5px;fill:url(#abf16437-76e4-4299-a12c-bb71e5b98d20)"/><polygon points="4.66 28.66 66.11 6.44 66.11 6.3 4.6 28.59 4.66 28.66" style="fill:#444545"/><polygon points="66.11 6.44 66.11 6.3 127.31 29.07 127.24 29.14 66.11 6.44" style="fill:#686868"/></g><g id="b7ce9272-76ea-485d-800b-ce25d60d9995" data-name="Jersey number"><text transform="translate(18.7 57.24) rotate(-8.42)" style="font-size:10px;fill:#fff;font-family:Montserrat-BoldItalic, Montserrat;font-weight:700;font-style:italic">27</text></g><g id="a5064fe6-9e2e-43a5-9331-bcde52d1133b" data-name="Name"><text transform="translate(18.54 74.38) rotate(-8.42)" style="font-size:12px;fill:#fff;font-family:Montserrat-BoldItalic, Montserrat;font-weight:700;font-style:italic" data-name="First Name">MIKE</text><text transform="translate(17.77 88.28) rotate(-8.42)" style="font-size:12px;fill:#fff;font-family:Montserrat-BoldItalic, Montserrat;font-weight:700;font-style:italic" data-name="Last Name">TROUT</text></g><g id="a6c31758-ea34-40de-ab75-77732b73efdd" data-name="Light Overlay"><polygon points="8.28 31.57 66.14 10.48 123.44 31.84 123.44 116.66 8.28 31.57" style="fill:url(#ad6c68c2-a413-4601-93d3-c164432a4344)"/></g><g id="ab2f3624-a73c-44a4-8d63-fda625e5d88b" data-name="Team color"><path d="M58,164.07,98,124.47a4.53,4.53,0,0,1,3-1.36h11.51a3.62,3.62,0,0,0,2.52-1c1.06-1.09,8.57-8.57,8.57-8.57v1.77l-48,48-9.77,3.51Z" transform="translate(0 0)" style="fill:#bf2d47"/><path d="M43.8,159.22l-11.23-4,16.74-16.69a4.82,4.82,0,0,1,3.39-1.39,5.12,5.12,0,0,0,4.51-1.48c2.07-2.05,47.52-47.52,47.52-47.52H77.84l45.7-46V80.89Z" transform="translate(0 0)" style="fill:#055da8"/></g><g id="a39a389f-1ecf-4aca-b150-2366e2b6a57e" data-name="Position"><text transform="translate(18.25 118.58) rotate(-8.42)" style="font-size:10px;fill:#fff;font-family:Montserrat-BoldItalic, Montserrat;font-weight:700;font-style:italic">CF</text><polygon points="18.71 105.63 18.71 106.65 27.13 105.38 27.13 104.34 18.71 105.63" style="fill:#fff"/></g><g id="b8c16f5e-0439-4c9e-a764-4d9a157f44d8" data-name="Playible logo"><path d="M60.44,33.06a9.13,9.13,0,0,1-.88-3.54V22.39H72.89v7.34a8.18,8.18,0,0,1-4.45,7.12L66.18,38a15.86,15.86,0,0,1-3.9-2.4l1.3-2.27H66.8L70,27.71l-1.62-2.8-6.5,0,1.66,2.82h3.26l-1.65,2.81H61.93Z" transform="translate(0 0)" style="fill:#fff"/></g></svg>'
            image_dict = xmltodict.parse(svg)

            # Change first name
            image_dict['svg']['g'][2]['text'][0]['#text'] = athlete.first_name.upper()
            # Change last name
            image_dict['svg']['g'][2]['text'][1]['#text'] = athlete.last_name.upper()
            # Change primary color
            image_dict['svg']['g'][4]['path'][1]['@style'] = 'fill: #' + athlete.team.primary_color  # 'fill: #000000'
            # Change secondary color
            image_dict['svg']['g'][4]['path'][0]['@style'] = 'fill: #' + athlete.team.secondary_color  # 'fill: #ffffff'
            # Change position
            image_dict['svg']['g'][5]['text']['#text'] = athlete.position
            # Change jersey number
            image_dict['svg']['g'][1]['text']['#text'] = str(athlete.jersey)

            image_xml = xmltodict.unparse(image_dict)

            f.write(image_xml)
            f.close()

            f = open(file_name, 'rb')

            file = File(f)
            athlete.nft_image.save(athlete_id + file_extension, file)

            f.close()

        return Response("ok")

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

        return game_teams

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


class GameTeamViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Manage game teams in the database"""
    queryset = GameTeam.objects.all()
    serializer_class = GameTeamCreateSerializer
    permission_classes = [AllowAny]
    lookup_field = 'id'

    action_serializers = {
        'create': GameTeamCreateSerializer,
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
