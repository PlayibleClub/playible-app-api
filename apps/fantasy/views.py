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

from terra_sdk.core.wasm.msgs import MsgExecuteContract

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
from apps.core.terra import create_and_sign_tx

from config.settings.base import ROOT_DIR, ADMIN_WALLET, OPEN_PACK_CONTRACT

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

    @ action(detail=False)
    def get_add_athletes_open_pack_msg(self, request):
        athlete_info = []

        athletes = Athlete.objects.filter(Q(api_id__in=[10009104, 10001087, 10008455, 10003268, 10000040, 10001958, 10009269, 10008438, 10000029, 10007421, 10006276, 10006099, 10009865, 10001105, 10007068, 10009589, 10005913, 10005250, 10006790, 10000780, 10005445, 10001961, 10000689, 10006622, 10001133, 10006826, 10003340, 10000809, 10001862, 10005377, 10005480, 10005839, 10000981, 10007010, 10006953, 10008662, 10006969, 10007647, 10006492, 10006717, 10006354, 10007075, 10009032, 10001270, 10001261, 10007419, 10006518, 10006394, 10006417, 10006807, 10008608, 10000381, 10009500, 10008369, 10007008, 10001072, 10000249, 10000637, 10005751, 10005910, 10000164, 10000165, 10000177, 10000453, 10001896, 10007062, 10001940, 10003163, 10003298, 10001827, 10000839, 10001161, 10000837, 10008360, 10006571, 10007641, 10008525, 10002001, 10008694, 10005307, 10006046, 10007727, 10006940, 10000492, 10009344, 10000084, 10000343, 10009296, 10002113, 10001182, 10001305, 10003212, 10000151, 10005302, 10001207, 10002054, 10008206, 10000258, 10006462, 10006154, 10000633, 10008437, 10000261, 10000998, 10008721, 10010464, 10006960, 10003133, 10001154, 10005879, 10005654, 10005575, 10000469, 10007024, 10008325, 10009298, 10001945, 10000312, 10000534, 10006804, 10002075, 10007359, 10007121, 10006212, 10000686, 10007781, 10002115, 10007028, 10006353, 10007245, 10000060, 10007294, 10006718, 10006506, 10008190, 10006695, 10006611, 10006439, 10005586, 10001910, 10010180, 10000352, 10005878, 10006088, 10001926, 10005660, 10009350, 10007055, 10007106, 10009253, 10007061, 10006418, 10000405, 10000601, 10002076, 10003204, 10005353, 10006345, 10006371, 10006344, 10006157, 10006637, 10007070, 10007277, 10000440, 10005351, 10005352, 10005835, 10005998, 10006172, 10007115, 10006871, 10007011, 10000494, 10000213, 10005308, 10000133, 10000438, 10011494, 10000301, 10006614, 10001871, 10007675, 10005650, 10006112, 10000155, 10009262, 10010729, 10007048, 10000845, 10000485, 10000719, 10003328, 10005405, 10000357, 10005589, 10006007, 10000481, 10006868, 10007148, 10007152, 10009010, 10009354, 10009116, 10003360, 10000432, 10007637, 10008767, 10007231, 10010605, 10002013, 10007427, 10000525, 10000353, 10005530, 10002059, 10001369, 10009140, 10010332, 10001901, 10008618, 10009338, 10007589, 10000613, 10005970, 10006760, 10009274, 10005210, 10008667, 10000600, 10008984, 10001361, 10000484, 10007049, 10008331, 10001132, 10005922, 10000768, 10007604, 10006662, 10006893, 10006902, 10000805, 10008769, 10002061, 10007341, 10007263, 10008338, 10007085, 10000176, 10000041, 10000077, 10000640, 10001091, 10001955, 10002094, 10003122, 10003192, 10007125, 10007046, 10003314, 10001325, 10005607, 10000618, 10000555, 10002049, 10000364, 10007299, 10000225, 10006085, 10000270, 10005191, 10000346, 10005472, 10007153, 10000685, 10009327, 10001946, 10005534, 10009155, 10007256, 10005448, 10008537, 10008429, 10008679,
                                          10007082, 10007151, 10001179, 10005433, 10000691, 10001010, 10006841, 10002074, 10007200, 10000539, 10000082, 10001889, 10008980, 10008358, 10006837, 10007058, 10007041, 10006935, 10007274, 10005264, 10010721, 10005288, 10001934, 10001918, 10005493, 10000775, 10000779, 10000857, 10007040, 10003219, 10009300, 10006008, 10007050, 10008431, 10000886, 10000095, 10010317, 10010327, 10006850, 10001077, 10001907, 10001911, 10005542, 10005722, 10006033, 10000900, 10001009, 10001085, 10000437, 10000770, 10006775, 10007009, 10007367, 10000787, 10000330, 10000426, 10000880, 10012307, 10005249, 10000217, 10002087, 10001966, 10000690, 10001313, 10005406, 10000777, 10007554, 10007117, 10001865, 10000397, 10005476, 10007655, 10000970, 10000986, 10008677, 10006466, 10002077, 10007398, 10006195, 10006200, 10001264, 10007090, 10006682, 10001971, 10003376, 10008439, 10006535, 10007096, 10006568, 10005569, 10002091, 10000242, 10008483, 10007035, 10006118, 10002005, 10005787, 10002093, 10000675, 10000731, 10001365, 10000439, 10006124, 10000859, 10009271, 10009878, 10007287, 10002082, 10008357, 10007006, 10000807, 10005232, 10008281, 10000746, 10007228, 10006053, 10007765, 10007111, 10005309, 10002045, 10005366, 10000344, 10006867, 10006512, 10005919, 10005664, 10006540, 10006299, 10000247, 10009582, 10009636, 10007144, 10006198, 10007217, 10007203, 10005672, 10000129, 10007416, 10007562, 10000530, 10001053, 10001943, 10001271, 10007812, 10005633, 10003312, 10006242, 10000273, 10005368, 10001234, 10005311, 10005315, 10001248, 10004421, 10000215, 10001129, 10001130, 10001222, 10003177, 10000646, 10006977, 10009268, 10005773, 10001209, 10000813, 10000958, 10005772, 10006767, 10006907, 10001191, 10000284, 10000071, 10002099, 10007043, 10005680, 10006044, 10001947, 10006284, 10009303, 10000311, 10008490, 10005834, 10001939, 10009359, 10006863, 10007284, 10007135, 10000020, 10003325, 10007369, 10010374, 10009285, 10005822, 10008749, 10000031, 10003149, 10001166, 10000393, 10000406, 10005741, 10007017, 10005503, 10008529, 10006792, 10008292, 10012277, 10001162, 10001250, 10003259, 10007033, 10006945, 10008332, 10001902, 10008561, 10008373, 10006272, 10006421, 10006431, 10007224, 10008199, 10001086, 10005684, 10001083, 10005384, 10001225, 10008458, 10008477, 10006566, 10009346, 10008425, 10000335, 10006184, 10008743, 10000908, 10001979, 10002089, 10008989, 10009516, 10001088, 10000593, 10006136, 10005628, 10007553, 10000394, 10007126, 10008798, 10002058, 10001253, 10007025, 10007407, 10008318, 10000499, 10007013, 10007501, 10007259, 10006072, 10007244, 10007535, 10005661, 10001181, 10009628, 10001908, 10008834, 10007100, 10001993, 10000101, 10000628, 10010409, 10009612, 10007039, 10001350, 10003368, 10000955, 10006794, 10001094, 10005299, 10007310, 10007911, 10000529, 10000953, 10006634, 10008378, 10001127, 10006992, 10006805, 10000007, 10009288, 10005800, 10005808, 10000425]))

        for athlete in athletes:
            token_uri = None

            try:
                if athlete.nft_image is not None:
                    token_uri = athlete.nft_image.url
            except:
                pass

            athlete_info.append({
                'athlete_id': str(athlete.id),
                'token_uri': token_uri,
                'symbol': str(athlete.api_id),
                'name': athlete.first_name + ' ' + athlete.last_name,
                'team': athlete.team.key,
                'position': athlete.position
            })

        msg = {
            'add_athletes': {
                'pack_type': 'starter',
                'athlete_info': athlete_info
            }
        }

        return Response(msg)

    @ action(detail=False, methods=['post'])
    def add_athletes_open_pack(self, request):
        msgs = []

        athletes = Athlete.objects.filter(Q(api_id__in=[10009104, 10001087, 10008455, 10003268, 10000040, 10001958, 10009269, 10008438, 10000029, 10007421, 10006276, 10006099, 10009865, 10001105, 10007068, 10009589, 10005913, 10005250, 10006790, 10000780, 10005445, 10001961, 10000689, 10006622, 10001133, 10006826, 10003340, 10000809, 10001862, 10005377, 10005480, 10005839, 10000981, 10007010, 10006953, 10008662, 10006969, 10007647, 10006492, 10006717, 10006354, 10007075, 10009032, 10001270, 10001261, 10007419, 10006518, 10006394, 10006417, 10006807, 10008608, 10000381, 10009500, 10008369, 10007008, 10001072, 10000249, 10000637, 10005751, 10005910, 10000164, 10000165, 10000177, 10000453, 10001896, 10007062, 10001940, 10003163, 10003298, 10001827, 10000839, 10001161, 10000837, 10008360, 10006571, 10007641, 10008525, 10002001, 10008694, 10005307, 10006046, 10007727, 10006940, 10000492, 10009344, 10000084, 10000343, 10009296, 10002113, 10001182, 10001305, 10003212, 10000151, 10005302, 10001207, 10002054, 10008206, 10000258, 10006462, 10006154, 10000633, 10008437, 10000261, 10000998, 10008721, 10010464, 10006960, 10003133, 10001154, 10005879, 10005654, 10005575, 10000469, 10007024, 10008325, 10009298, 10001945, 10000312, 10000534, 10006804, 10002075, 10007359, 10007121, 10006212, 10000686, 10007781, 10002115, 10007028, 10006353, 10007245, 10000060, 10007294, 10006718, 10006506, 10008190, 10006695, 10006611, 10006439, 10005586, 10001910, 10010180, 10000352, 10005878, 10006088, 10001926, 10005660, 10009350, 10007055, 10007106, 10009253, 10007061, 10006418, 10000405, 10000601, 10002076, 10003204, 10005353, 10006345, 10006371, 10006344, 10006157, 10006637, 10007070, 10007277, 10000440, 10005351, 10005352, 10005835, 10005998, 10006172, 10007115, 10006871, 10007011, 10000494, 10000213, 10005308, 10000133, 10000438, 10011494, 10000301, 10006614, 10001871, 10007675, 10005650, 10006112, 10000155, 10009262, 10010729, 10007048, 10000845, 10000485, 10000719, 10003328, 10005405, 10000357, 10005589, 10006007, 10000481, 10006868, 10007148, 10007152, 10009010, 10009354, 10009116, 10003360, 10000432, 10007637, 10008767, 10007231, 10010605, 10002013, 10007427, 10000525, 10000353, 10005530, 10002059, 10001369, 10009140, 10010332, 10001901, 10008618, 10009338, 10007589, 10000613, 10005970, 10006760, 10009274, 10005210, 10008667, 10000600, 10008984, 10001361, 10000484, 10007049, 10008331, 10001132, 10005922, 10000768, 10007604, 10006662, 10006893, 10006902, 10000805, 10008769, 10002061, 10007341, 10007263, 10008338, 10007085, 10000176, 10000041, 10000077, 10000640, 10001091, 10001955, 10002094, 10003122, 10003192, 10007125, 10007046, 10003314, 10001325, 10005607, 10000618, 10000555, 10002049, 10000364, 10007299, 10000225, 10006085, 10000270, 10005191, 10000346, 10005472, 10007153, 10000685, 10009327, 10001946, 10005534, 10009155, 10007256, 10005448, 10008537, 10008429, 10008679,
                                                        10007082, 10007151, 10001179, 10005433, 10000691, 10001010, 10006841, 10002074, 10007200, 10000539, 10000082, 10001889, 10008980, 10008358, 10006837, 10007058, 10007041, 10006935, 10007274, 10005264, 10010721, 10005288, 10001934, 10001918, 10005493, 10000775, 10000779, 10000857, 10007040, 10003219, 10009300, 10006008, 10007050, 10008431, 10000886, 10000095, 10010317, 10010327, 10006850, 10001077, 10001907, 10001911, 10005542, 10005722, 10006033, 10000900, 10001009, 10001085, 10000437, 10000770, 10006775, 10007009, 10007367, 10000787, 10000330, 10000426, 10000880, 10012307, 10005249, 10000217, 10002087, 10001966, 10000690, 10001313, 10005406, 10000777, 10007554, 10007117, 10001865, 10000397, 10005476, 10007655, 10000970, 10000986, 10008677, 10006466, 10002077, 10007398, 10006195, 10006200, 10001264, 10007090, 10006682, 10001971, 10003376, 10008439, 10006535, 10007096, 10006568, 10005569, 10002091, 10000242, 10008483, 10007035, 10006118, 10002005, 10005787, 10002093, 10000675, 10000731, 10001365, 10000439, 10006124, 10000859, 10009271, 10009878, 10007287, 10002082, 10008357, 10007006, 10000807, 10005232, 10008281, 10000746, 10007228, 10006053, 10007765, 10007111, 10005309, 10002045, 10005366, 10000344, 10006867, 10006512, 10005919, 10005664, 10006540, 10006299, 10000247, 10009582, 10009636, 10007144, 10006198, 10007217, 10007203, 10005672, 10000129, 10007416, 10007562, 10000530, 10001053, 10001943, 10001271, 10007812, 10005633, 10003312, 10006242, 10000273, 10005368, 10001234, 10005311, 10005315, 10001248, 10004421, 10000215, 10001129, 10001130, 10001222, 10003177, 10000646, 10006977, 10009268, 10005773, 10001209, 10000813, 10000958, 10005772, 10006767, 10006907, 10001191, 10000284, 10000071, 10002099, 10007043, 10005680, 10006044, 10001947, 10006284, 10009303, 10000311, 10008490, 10005834, 10001939, 10009359, 10006863, 10007284, 10007135, 10000020, 10003325, 10007369, 10010374, 10009285, 10005822, 10008749, 10000031, 10003149, 10001166, 10000393, 10000406, 10005741, 10007017, 10005503, 10008529, 10006792, 10008292, 10012277, 10001162, 10001250, 10003259, 10007033, 10006945, 10008332, 10001902, 10008561, 10008373, 10006272, 10006421, 10006431, 10007224, 10008199, 10001086, 10005684, 10001083, 10005384, 10001225, 10008458, 10008477, 10006566, 10009346, 10008425, 10000335, 10006184, 10008743, 10000908, 10001979, 10002089, 10008989, 10009516, 10001088, 10000593, 10006136, 10005628, 10007553, 10000394, 10007126, 10008798, 10002058, 10001253, 10007025, 10007407, 10008318, 10000499, 10007013, 10007501, 10007259, 10006072, 10007244, 10007535, 10005661, 10001181, 10009628, 10001908, 10008834, 10007100, 10001993, 10000101, 10000628, 10010409, 10009612, 10007039, 10001350, 10003368, 10000955, 10006794, 10001094, 10005299, 10007310, 10007911, 10000529, 10000953, 10006634, 10008378, 10001127, 10006992, 10006805, 10000007, 10009288, 10005800, 10005808, 10000425])).order_by('pk')
        counter = 1
        athlete_info = []

        for athlete in athletes:
            token_uri = None

            try:
                if athlete.nft_image is not None:
                    token_uri = athlete.nft_image.url
            except:
                pass

            athlete_info.append({
                'athlete_id': str(athlete.id),
                'token_uri': token_uri,
                'symbol': str(athlete.api_id),
                'name': athlete.first_name + ' ' + athlete.last_name,
                'team': athlete.team.key,
                'position': athlete.position
            })

            if len(athlete_info) == 30 or counter == len(athletes):
                add_athletes_msg = {
                    "add_athletes": {
                        "pack_type": "starter",
                        "athlete_info": athlete_info
                    }
                }

                msg_execute = MsgExecuteContract(
                    ADMIN_WALLET,
                    OPEN_PACK_CONTRACT,
                    add_athletes_msg
                )
                msgs.append(msg_execute)

                athlete_info = []

            counter += 1

        create_and_sign_tx(msgs)

        return Response("success")


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
        games = Game.objects.filter(Q(end_datetime__lte=now))
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
                            'fantasy_score': fantasy_score,
                            'nft_image': None
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
                'fantasy_score': fantasy_score,
                'nft_image': None
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
