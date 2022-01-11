
from django.conf import settings

def parse_team_list_data(data):
  teams = []
  for team in data:
    teams.append({
      "location": team.get('City'),
      "name": team.get('Name'),
      "api_id": team.get('TeamID')
    })
  return teams

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

#Use this for printing
def print_debug(string):
    if(settings.DEBUG):
        print(string)