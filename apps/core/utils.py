
from functools import wraps

from django.conf import settings
from django.db.models import QuerySet

from rest_framework.response import Response


def paginate(func):

    @wraps(func)
    def inner(self, *args, **kwargs):
        queryset = func(self, *args, **kwargs)
        assert isinstance(queryset, (list, QuerySet)), "apply_pagination expects a List or a QuerySet"

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)
    return inner


def parse_team_list_data(data):
    teams = []

    for team in data:
        teams.append({
            "location": team.get('City'),
            "name": team.get('Name'),
            "api_id": team.get('TeamID'),
            "primary_color": team.get('PrimaryColor'),
            "secondary_color": team.get('SecondaryColor'),
        })
    return teams


def parse_athlete_stat_data(data):
    athletes = []

    for athlete in data:
        athletes.append({
            'api_id': athlete.get('PlayerID'),
            "team_id": athlete.get('TeamID'),
            "fantasy_score": athlete.get('FantasyPointsDraftKings'),
            "singles": athlete.get('Singles'),
            "doubles": athlete.get('Doubles'),
            "triples": athlete.get('Triples'),
            "home_runs": athlete.get('HomeRuns'),
            "runs_batted_in": athlete.get('RunsBattedIn'),
            "walks": athlete.get('Walks'),
            "hit_by_pitch": athlete.get('HitByPitch'),
            "stolen_bases": athlete.get('StolenBases'),
            "position": athlete.get('Position'),
        })

    return athletes


def parse_athlete_list_data(data):
    athletes = []
    for athlete in data:
        if athlete.get('Status') == "Active":
            athletes.append({
                'first_name': athlete.get('FirstName'),
                'last_name': athlete.get('LastName'),
                'api_id': athlete.get('PlayerID'),
                'team_id': athlete.get('TeamID'),
                'position': athlete.get('Position'),
                'salary': athlete.get('Salary', 0),
                'jersey': athlete.get('Jersey'),
                'is_active': athlete.get('Status'),
                'is_injured': athlete.get('InjuryStatus')
            })
    return athletes


def filter_athlete_data(data, participant):
    athlete_list = data.get('league').get('players')
    for athlete in athlete_list:
        if participant.get('api_id', None) is not None:
            if athlete.get('playerId') == participant.get('api_id'):
                return {
                    'first_name': player.get('firstName'),
                    'last_name': player.get('lastName'),
                    'terra_id': participant.get('terra_id'),
                    'api_id': player.get('playerId'),
                    'team': player.get('team').get('teamId'),
                    'positions': player.get('positions'),
                    'is_active': player.get('isActive'),
                    'is_injured': player.get('isInjured'),
                    'is_suspended': player.get('isSuspended')
                }
        else:
            if player.get('firstName', '').lower() == participant.get('first_name').lower() and player.get('lastName', '').lower() == participant.get('last_name').lower():
                return {
                    'first_name': player.get('firstName'),
                    'last_name': player.get('lastName'),
                    'terra_id': participant.get('terra_id'),
                    'api_id': player.get('playerId'),
                    'team': player.get('team').get('teamId'),
                    'positions': player.get('positions'),
                    'is_active': player.get('isActive'),
                    'is_injured': player.get('isInjured'),
                    'is_suspended': player.get('isSuspended')
                }
    raise Exception("No matching data found")


def parse_athlete_season_data(data, participant):
    athlete_season_data = data.get('league').get('players')[0].get('seasons')[0]

    return {
        'season': athlete_season_data.get('season'),
        'points': athlete_season_data.get('points'),
        'rebounds': athlete_season_data.get('rebounds'),
        'assists': athlete_season_data.get('assists'),
        'blocks': athlete_season_data.get('blocks'),
        'turnovers': athlete_season_data.get('turnovers')
    }

# Use this for printing


def print_debug(string):
    if(settings.DEBUG):
        print(string)
