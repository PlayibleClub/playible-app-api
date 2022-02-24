from datetime import datetime, timedelta

from django.shortcuts import render
from django.db.models import Q
from django.conf import settings
from django.utils import timezone

from rest_framework import status, generics, viewsets, mixins
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from apps.fantasy import requests
from apps.account import models, serializers
from apps.core import utils, terra
from apps.fantasy.models import Athlete, GameSchedule

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

            now = timezone.now()

            season = now.strftime('%Y').upper()
            season = '2021'
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
