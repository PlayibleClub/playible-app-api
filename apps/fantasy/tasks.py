import decimal

from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from config import celery_app

from apps.fantasy import requests
from apps.fantasy.models import Game
from apps.core import utils

User = get_user_model()


@celery_app.task()
def update_team_scores():
    """Task for updating all active games' teams scores per day"""

    now = timezone.now()

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
                game_team.save()

        return len(games)
    else:
        content = {
            "message": "Failed to fetch data from Stats Perform API",
            "response": response['response']
        }

        return content
