from datetime import datetime, timedelta
import decimal
import pytz

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from config import celery_app

from apps.fantasy import requests
from apps.fantasy.models import Athlete, Game, GameAthleteStat, GameTeam
from apps.core import utils

User = get_user_model()


@celery_app.task()
def update_team_scores():
    """Task for updating all active games' teams scores per day"""

    # Task will run every 11:55 PM EST / 12:55 PM (next day) Manila time, so subtract -1 to day to get previous day since default timezone of Django is Asia/Manila
    now = timezone.now() - timedelta(days=1)

    date_query = now.strftime('%Y-%b-%d').upper()
    url = 'stats/json/PlayerGameStatsByDate/' + date_query

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

        return len(games)
    else:
        content = {
            "message": "Failed to fetch data from Stats Perform API",
            "response": response['response']
        }

        return content


@celery_app.task()
def update_athlete_stats():
    """Task for updating all athlete stats on the current season"""

    now = timezone.now()

    season = now.strftime('%Y').upper()
    # season = '2021'
    url = 'stats/json/PlayerSeasonStats/' + season

    response = requests.get(url)

    if response['status'] == settings.RESPONSE['STATUS_OK']:
        athlete_data = utils.parse_athlete_stat_data(response['response'])

        new_athlete_stats = []
        existing_athlete_stats = []

        for athlete in athlete_data:
            athlete_obj = Athlete.objects.filter(api_id=athlete.get('api_id')).first()

            if athlete_obj:
                athlete_stat_obj = GameAthleteStat.objects.filter(Q(athlete=athlete_obj) & Q(season=season)).first()

                if athlete_stat_obj is None:
                    athlete_stat_obj = GameAthleteStat(
                        season=season,
                        athlete=athlete_obj,
                        fantasy_score=athlete.get('fantasy_score'),
                        singles=athlete.get('singles'),
                        doubles=athlete.get('doubles'),
                        triples=athlete.get('triples'),
                        home_runs=athlete.get('home_runs'),
                        runs_batted_in=athlete.get('runs_batted_in'),
                        walks=athlete.get('walks'),
                        hit_by_pitch=athlete.get('hit_by_pitch'),
                        stolen_bases=athlete.get('stolen_bases'),
                        position=athlete.get('position'),
                    )

                    new_athlete_stats.append(athlete_stat_obj)
                else:
                    athlete_stat_obj.fantasy_score = athlete.get('fantasy_score')
                    athlete_stat_obj.singles = athlete.get('singles')
                    athlete_stat_obj.doubles = athlete.get('doubles')
                    athlete_stat_obj.triples = athlete.get('triples')
                    athlete_stat_obj.home_runs = athlete.get('home_runs')
                    athlete_stat_obj.runs_batted_in = athlete.get('runs_batted_in')
                    athlete_stat_obj.walks = athlete.get('walks')
                    athlete_stat_obj.hit_by_pitch = athlete.get('hit_by_pitch')
                    athlete_stat_obj.stolen_bases = athlete.get('stolen_bases')
                    athlete_stat_obj.position = athlete.get('position')

                    existing_athlete_stats.append(athlete_stat_obj)

        GameAthleteStat.objects.bulk_create(new_athlete_stats)
        GameAthleteStat.objects.bulk_update(
            existing_athlete_stats,
            ['fantasy_score', 'singles', 'doubles', 'triples', 'home_runs',
                'runs_batted_in', 'walks', 'hit_by_pitch', 'stolen_bases', 'position'],
            20
        )

        return(len(new_athlete_stats) + len(existing_athlete_stats))
