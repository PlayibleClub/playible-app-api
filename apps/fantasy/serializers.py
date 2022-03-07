from apps.account.models import Collection
from rest_framework import serializers, status, validators

from apps.fantasy.models import *
from apps.core import utils

# Fantasy data serializers


class TeamListSerializer(serializers.ListSerializer):
    def save(self):
        teams_list = []
        for team_data in self.validated_data:
            team, is_created = Team.objects.get_or_create(
                api_id=team_data['api_id'],
                defaults={
                    'location': team_data['location'],
                    'name': team_data['name'],
                }
            )
            teams_list.append({
                "is_created": is_created,
                "data": team
            })
        return {
            'message': "Teams added.",
            'data': teams_list
        }


class TeamSerializer(serializers.ModelSerializer):
    location = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_null=True)
    api_id = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    class Meta:
        model = Team
        fields = ['id', 'location', 'name', 'api_id']
        read_only_fields = ['id']
        list_serializer_class = TeamListSerializer


class TeamDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ['id',  'name', 'api_id']

# Serializer for Stats Perform API data


class AthleteAPISerializer(serializers.ModelSerializer):
    team_id = serializers.IntegerField()
    is_active = serializers.CharField(allow_null=True)
    is_injured = serializers.CharField(allow_null=True)
    #positions = serializers.PrimaryKeyRelatedField(queryset=Position.objects.all(), many=True)
    #positions = PositionSerializer(many=True)

    class Meta:
        model = Athlete
        fields = [
            'first_name',
            'last_name',
            'api_id',
            'team_id',
            'position',
            'salary',
            'jersey',
            'is_active',
            'is_injured'
        ]
        extra_kwargs = {
            'team_id': {'write_only': True},
            'is_active': {'write_only': True},
            'is_injured': {'write_only': True}
        }

    def validate(self, data):
        if data['is_active'] == 'Active':
            data['is_active'] = True
        else:
            data['is_active'] = False

        if data['is_injured'] is None:
            data['is_injured'] = False
        else:
            data['is_injured'] = True

        data['team'] = Team.objects.get(api_id=data['team_id'])
        data['team_id'] = data['team'].id
        return data

    def save(self):
        if self.instance is not None:
            self.instance.first_name = self.validated_data.get('first_name')
            self.instance.last_name = self.validated_data.get('last_name')
            self.instance.api_id = self.validated_data.get('api_id')
            self.instance.position = self.validated_data.get('position')
            self.instance.salary = self.validated_data.get('salary')
            self.instance.jersey = self.validated_data.get('jersey')
            self.instance.is_active = self.validated_data.get('is_active')
            self.instance.is_injured = self.validated_data.get('is_injured')
            self.instance.team = self.validated_data.get('team')
        else:
            athlete = Athlete(
                first_name=self.validated_data['first_name'],
                last_name=self.validated_data['last_name'],
                api_id=self.validated_data['api_id'],
                position=self.validated_data['position'],
                salary=self.validated_data['salary'],
                jersey=self.validated_data['jersey'],
                is_active=self.validated_data['is_active'],
                is_injured=self.validated_data['is_injured'],
                team=self.validated_data.get('team'),
            )
            athlete.save()

        return {
            'message': "Athlete added.",
            'id': athlete.pk
        }


class AthleteSerializer(serializers.ModelSerializer):
    team = TeamDetailSerializer(read_only=True)

    class Meta:
        model = Athlete
        fields = [
            'id',
            'first_name',
            'last_name',
            'api_id',
            'team',
            'position',
            'salary',
            'jersey',
            'is_active',
            'is_injured',
        ]


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = [
            'id',
            'name',
            'start_datetime',
            'end_datetime',
            'prize',
            'image'
        ]


class GameCreateSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    start_datetime = serializers.DateTimeField()
    duration = serializers.IntegerField()

    class Meta:
        model = Game
        fields = [
            'name',
            'start_datetime',
            'duration',
            'prize',
            'image'
        ]


class GameAthleteSerializer(serializers.Serializer):
    athlete_id = serializers.IntegerField()
    token_id = serializers.CharField()
    contract_addr = serializers.CharField()


class GameTeamListDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameTeam
        fields = ['id', 'name', 'fantasy_score', 'created_at']


class GameTeamAccountLeaderboardDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['wallet_addr']


class GameTeamLeaderboardSerializer(serializers.ModelSerializer):
    account = GameTeamAccountLeaderboardDetailSerializer(read_only=True)

    class Meta:
        model = GameTeam
        fields = [
            'name',
            'fantasy_score',
            'account'
        ]


class GameTeamCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    game = serializers.IntegerField()
    wallet_addr = serializers.CharField()
    athletes = serializers.ListField(child=GameAthleteSerializer())

    def validate(self, data):
        game_id = data['game']
        athletes = data['athletes']

        errors = []
        game_obj = None
        athlete_objs = []

        # Check if game id exists
        try:
            game_obj = Game.objects.get(id=game_id)
            data['game_obj'] = game_obj
        except Game.DoesNotExist:
            errors.append('Game does not exist.')

        # Check if all athletes exist in db
        for athlete in athletes:
            athlete_id = athlete['athlete_id']

            try:
                athlete = Athlete.objects.get(id=athlete_id)
                athlete_objs.append(athlete)
            except Athlete.DoesNotExist:
                errors.append(f'Athlete {athlete_id} does not exist.')

        if len(errors):
            error_message = {'errors': errors}
            raise serializers.ValidationError(error_message)

        data['athlete_objs'] = athlete_objs

        return data

    def create(self, validated_data):
        name = validated_data['name']
        game = validated_data['game_obj']
        wallet_addr = validated_data['wallet_addr']
        athlete_objs = validated_data['athlete_objs']
        athletes = validated_data['athletes']

        account, created = Account.objects.get_or_create(
            username=wallet_addr,
            wallet_addr=wallet_addr
        )

        game_team = GameTeam.objects.create(
            name=name,
            game=game,
            account=account
        )

        for index, athlete_obj in enumerate(athlete_objs):
            collection, created = Collection.objects.get_or_create(
                contract_addr=athletes[index]['contract_addr']
            )
            asset, created = Asset.objects.get_or_create(
                token_id=athletes[index]['token_id'],
                owner=account,
                collection=collection
            )
            game_athlete, created = GameAthlete.objects.get_or_create(
                game=game,
                athlete=athlete_obj,
            )
            game_asset, created = GameAsset.objects.get_or_create(
                game_team=game_team,
                game_athlete=game_athlete,
                asset=asset
            )
            # game_athlete_stat, created = GameAthleteStat.objects.get_or_create(
            #     game_athlete=game_athlete,
            # )

        return game_team


class AccountLeaderboardSerializer(serializers.Serializer):
    address = serializers.CharField()
    fantasy_score = serializers.IntegerField()
    rank = serializers.IntegerField()


class GameLeaderboardSerializer(serializers.Serializer):
    prize = serializers.IntegerField()
    winners = AccountLeaderboardSerializer(many=True)


class BlankSerializer(serializers.Serializer):
    pass


class PackAddressDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackAddress
        fields = ['release', 'open_pack_addr', 'token_addr']


class AthleteGameStatDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Athlete
        fields = [
            'id',
            'first_name',
            'last_name',
            'api_id',
        ]


class AthleteStatDetailSerializer(serializers.ModelSerializer):
    athlete = AthleteGameStatDetailSerializer(read_only=True)

    class Meta:
        model = GameAthleteStat
        fields = ['athlete', 'fantasy_score', 'singles', 'doubles', 'triples', 'home_runs',
                  'runs_batted_in', 'walks', 'hit_by_pitch', 'stolen_bases', 'position']
