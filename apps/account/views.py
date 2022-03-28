from datetime import datetime, timedelta

from django.shortcuts import render
from django.db.models import Q
from django.conf import settings
from django.utils import timezone

from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from config.settings.base import GAME_CONTRACT

from apps.fantasy import requests
from apps.account import models, serializers
from apps.core import utils, terra
from apps.fantasy.models import Athlete, GameAthleteStat, GameSchedule, GameTeam

# TODO: Define permissions for create and update actions


class BaseViewSet(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin
                  ):
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

    @swagger_auto_schema(auto_schema=None)
    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_403_FORBIDDEN)


class CollectionViewSet(BaseViewSet):
    """Manage collections in the database"""
    queryset = models.Collection.objects.all()
    serializer_class = serializers.CollectionSerializer
    permission_classes = [AllowAny]
    '''
    def create(self, request, *args, **kwargs):
        try:
            collection = models.Collection.objects.get(collection__pk = request.data.get('collection'))
            serializer = self.get_serializer(collection, data=request.data)
        except models.Collection.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
        if(serializer.is_valid()):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            content = serializer.errors
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
    '''


class AccountViewset(BaseViewSet):
    """Manage accounts in the database"""
    queryset = models.Account.objects.all()
    serializer_class = serializers.AccountSerializer
    permission_classes = [AllowAny]

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


class AssetViewset(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin,
                   mixins.RetrieveModelMixin):
    """Manage assets in the database"""
    queryset = models.Asset.objects.all()
    serializer_class = serializers.AssetSerializer
    permission_classes = [AllowAny]

    '''
    def partial_update(self, request, *args, **kwargs):
        table_object = self.get_object()
        data = request.data

        try:
            owner = models.Account.objects.get(id=data["id"])
            table_object.owner = owner
        except KeyError:
            pass

        try:
            collection = models.Collection.objects.get(id=data["id"])
            table_object.collection = collection
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
    '''


class AccountAssetView(generics.GenericAPIView):
    queryset = models.Asset.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.AssetSerializer

    def get(self, request, wallet=None, contract=None):
        account, is_created = models.Account.objects.get_or_create(
            wallet_addr=wallet
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=contract
        )

        response = terra.query_contract(contract, {"tokens": {"owner": wallet}})
        assets = models.Asset.objects.none()
        for token in response['tokens']:
            asset, is_created = models.Asset.objects.get_or_create(
                token_id=token,
                owner=account,
                collection=collection,
            )
            assets = assets.union(models.Asset.objects.filter(pk=asset.pk))
        serializer = self.serializer_class(assets, many=True)
        #user = User.objects.get(username=request.user)
        #queryset = models.UserAddress.objects.filter(user=user)
        #serializer = serializers.UserAddressSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AthleteTokenView(generics.GenericAPIView):
    queryset = models.Asset.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.AssetSerializer

    def get(self, request, wallet=None, contract=None):
        account, is_created = models.Account.objects.get_or_create(
            wallet_addr=wallet
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=contract
        )

        limit = self.request.query_params.get('limit', None)
        start_after = self.request.query_params.get('start_after', None)

        msg = {"owner_tokens_info": {"owner": wallet}}
        # total_tokens_msg = {"owner_num_tokens": {"owner": wallet}}

        # if start_after:
        #     msg['all_tokens_info']['start_after'] = start_after

        # total_tokens = terra.query_contract(contract, total_tokens_msg)

        # if limit:
        #     msg['all_tokens_info']['limit'] = int(limit)
        # else:
        #     if total_tokens:
        #         msg['all_tokens_info']['limit'] = total_tokens

        response = terra.query_contract(contract, msg)

        game_ids = list(GameTeam.objects.filter(Q(account=account)).order_by(
            'game__id').distinct('game__id').values_list('game__id', flat=True))
        locked_token_ids = []

        # Start of loop per game id
        for game_id in game_ids:
            player_info_msg = {
                "player_info": {
                    "game_id": str(game_id),
                    "player_addr": wallet
                }
            }
            player_info_res = terra.query_contract(GAME_CONTRACT, player_info_msg)

            if player_info_res['is_claimed'] == False:
                locked_token_ids += player_info_res['locked_tokens']
        # End of loop per game id

        try:
            tokens = response
            athlete_ids = []
            athletes = []

            for token in tokens:
                if "fantasy_score" not in token:
                    token['fantasy_score'] = 0
                    token['singles'] = 0
                    token['doubles'] = 0
                    token['triples'] = 0
                    token['home_runs'] = 0
                    token['runs_batted_in'] = 0
                    token['walks'] = 0
                    token['hit_by_pitch'] = 0
                    token['stolen_bases'] = 0
                    token['position'] = None
                    token['nft_image'] = None
                    token['is_locked'] = False

            for locked_token_id in locked_token_ids:
                all_nft_info_msg = {
                    "all_nft_info": {
                        "token_id": locked_token_id
                    }
                }
                all_nft_info_res = terra.query_contract(contract, all_nft_info_msg)
                tokens.append({
                    'token_id': locked_token_id,
                    'token_info': all_nft_info_res,
                    'fantasy_score': 0,
                    'singles': 0,
                    'doubles': 0,
                    'triples': 0,
                    'home_runs': 0,
                    'runs_batted_in': 0,
                    'walks': 0,
                    'hit_by_pitch': 0,
                    'stolen_bases': 0,
                    'position': None,
                    'nft_image': None,
                    'is_locked': True
                })
                athlete_id = int(all_nft_info_res['info']['extension']['athlete_id'])
                athlete_ids.append(athlete_id)

            now = timezone.now()
            season = now.strftime('%Y').upper()

            for token in tokens:
                # Retrieve fantasy score for each token based on game sched
                athlete_id = int(token['token_info']['info']['extension']['athlete_id'])
                athlete_ids.append(athlete_id)

            athletes = Athlete.objects.filter(id__in=athlete_ids)
            athlete_stats = GameAthleteStat.objects.filter(Q(athlete__id__in=athlete_ids) & Q(season=season))

            for token in tokens:
                # Retrieve fantasy score for each token based on game sched
                athlete_id = int(token['token_info']['info']['extension']['athlete_id'])
                athlete = next((item for item in athletes if item.id == athlete_id), None)

                if athlete:
                    # Search athlete if it has a stat data
                    athlete_stat = next((item for item in athlete_stats if item.athlete.id == athlete_id), None)

                    if athlete_stat:
                        token['fantasy_score'] += athlete_stat.fantasy_score
                        token['singles'] += athlete_stat.singles
                        token['doubles'] += athlete_stat.doubles
                        token['triples'] += athlete_stat.triples
                        token['home_runs'] += athlete_stat.home_runs
                        token['runs_batted_in'] += athlete_stat.runs_batted_in
                        token['walks'] += athlete_stat.walks
                        token['hit_by_pitch'] += athlete_stat.hit_by_pitch
                        token['stolen_bases'] += athlete_stat.stolen_bases

                    token['position'] = athlete.position

                    if athlete.nft_image:
                        token['nft_image'] = athlete.nft_image.url

            return Response({"total_count": len(tokens), "tokens": tokens}, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AthleteTokenView2(generics.GenericAPIView):
    queryset = models.Asset.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.AssetSerializer

    def get(self, request, wallet=None, contract=None):
        account, is_created = models.Account.objects.get_or_create(
            wallet_addr=wallet
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=contract
        )

        response = terra.query_contract(contract, {"all_tokens_info": {"owner": wallet}})

        try:
            tokens = response

            for token in tokens:
                if "fantasy_score" not in token:
                    token['fantasy_score'] = 0
                    token['singles'] = 0
                    token['doubles'] = 0
                    token['triples'] = 0
                    token['home_runs'] = 0
                    token['runs_batted_in'] = 0
                    token['walks'] = 0
                    token['hit_by_pitch'] = 0
                    token['stolen_bases'] = 0
                    token['position'] = None

            now = timezone.now()

            season = now.strftime('%Y').upper()
            url = 'stats/json/PlayerSeasonStats/' + season

            response = requests.get(url)

            if response['status'] == settings.RESPONSE['STATUS_OK']:
                athlete_data = utils.parse_athlete_stat_data(response['response'])

                for token in tokens:
                    # Retrieve fantasy score for each token based on game sched
                    athlete_id = int(token['token_info']['info']['extension']['athlete_id'])
                    athlete = Athlete.objects.filter(pk=athlete_id).first()

                    if athlete:
                        # Search athlete if it has a stat data
                        data = next((item for item in athlete_data if item["api_id"] == athlete.api_id), None)

                        if data:
                            token['fantasy_score'] += data['fantasy_score']
                            token['singles'] += data['singles']
                            token['doubles'] += data['doubles']
                            token['triples'] += data['triples']
                            token['home_runs'] += data['home_runs']
                            token['runs_batted_in'] += data['runs_batted_in']
                            token['walks'] += data['walks']
                            token['hit_by_pitch'] += data['hit_by_pitch']
                            token['stolen_bases'] += data['stolen_bases']
                            token['position'] = data['position']
            else:
                print('FAIL FETCH DATA')

            return Response(tokens, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AthleteTokenView3(generics.GenericAPIView):
    queryset = models.Asset.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.AssetSerializer

    def get(self, request, wallet=None, contract=None):
        account, is_created = models.Account.objects.get_or_create(
            wallet_addr=wallet
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=contract
        )

        response = terra.query_contract(contract, {"all_tokens_info": {"owner": wallet}})

        try:
            tokens = response

            for token in tokens:
                if "fantasy_score" not in token:
                    token['fantasy_score'] = 0

            now = datetime.now()  # TODO: CHANGE TO THIS
            # now = datetime(2022, 3, 31, 0, 0)

            # This date range gets the monday of this week until Sunday
            start_date = now - timedelta(days=now.weekday())
            end_date = start_date + timedelta(days=6)

            # Get distinct game schedule dates within the date range
            game_schedules = GameSchedule.objects.filter(
                Q(datetime__date__gte=start_date) & Q(datetime__date__lte=end_date)).order_by('datetime').values('datetime').distinct()

            # print('game schedules')
            # print(game_schedules[0]['datetime'])
            # print(game_schedules[0]['datetime'].strftime('%Y'))
            # game_schedules = [{'datetime': datetime(2017, 9, 1, 0, 0)}]

            for game_schedule in game_schedules:
                # Query fantasy api for player stats on this schedule
                cur_date = game_schedule['datetime'].strftime('%Y-%b-%d').upper()
                url = 'stats/json/PlayerGameStatsByDate/' + cur_date

                response = requests.get(url)

                if response['status'] == settings.RESPONSE['STATUS_OK']:
                    athlete_data = utils.parse_athlete_stat_data(response['response'])

                    for token in tokens:
                        # Retrieve fantasy score for each token based on game sched
                        athlete_id = int(token['token_info']['info']['extension']['athlete_id'])
                        athlete = Athlete.objects.filter(pk=athlete_id).first()

                        if athlete:
                            # Search athlete if it has a stat data
                            data = next((item for item in athlete_data if item["api_id"] == athlete.api_id), None)

                            if data:
                                token['fantasy_score'] += data['fantasy_score']
                else:
                    print('FAIL FETCH DATA')

            return Response(tokens, status=status.HTTP_200_OK)
        except:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class AccountAssetView(generics.GenericAPIView):
    queryset = models.Asset.objects.all()
    permission_classes = [AllowAny]
    serializer_class = serializers.AssetSerializer

    def get(self, request, wallet=None, contract=None):
        account, is_created = models.Account.objects.get_or_create(
            wallet_addr=wallet
        )
        collection, is_created = models.Collection.objects.get_or_create(
            contract_addr=contract
        )

        response = terra.query_contract(contract, {"tokens": {"owner": wallet}})
        assets = models.Asset.objects.none()
        for token in response['tokens']:
            asset, is_created = models.Asset.objects.get_or_create(
                token_id=token,
                owner=account,
                collection=collection,
            )
            assets = assets.union(models.Asset.objects.filter(pk=asset.pk))
        serializer = self.serializer_class(assets, many=True)
        #user = User.objects.get(username=request.user)
        #queryset = models.UserAddress.objects.filter(user=user)
        #serializer = serializers.UserAddressSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmailViewset(viewsets.GenericViewSet,
                   mixins.ListModelMixin,
                   mixins.CreateModelMixin
                   ):
    """Manage prelaunch emails in the database"""
    queryset = models.PrelaunchEmail.objects.all()
    serializer_class = serializers.EmailSerializer

    def get_permissions(self):
        """Set custom permissions for each action."""
        if self.action in ['list']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['create']:
            self.permission_classes = [AllowAny]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Create a new prelaunch email"""
        if(serializer.is_valid()):
            content = serializer.save()
            return Response(content, status=status.HTTP_201_CREATED)
        else:
            content = serializer.errors
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class SalesOrderViewset(BaseViewSet):
    """Manage sales order in the database"""
    queryset = models.SalesOrder.objects.all()
    serializer_class = serializers.SalesOrderSerializer
    permission_classes = [AllowAny]
