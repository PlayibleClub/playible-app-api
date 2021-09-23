
from django.conf import settings

def parse_team_list_data(data):
  try: 
    conference_list = data.get('league').get('season').get('conferences')
    teams = []
    for conference in conference_list:
      for division in conference.get('divisions'):
        for team in division.get('teams'):
          teams.append({
            "location": team.get('location'),
            "nickname": team.get('nickname'),
            "api_id": team.get('teamId')
          })
    return teams

  except:
    print_debug("Invalid team data")

def filter_participant_data(data, participant):
  try:
    player_list = data.get('league').get('players')
    for player in player_list:
      if participant.get('api_id', None) is not None:
        if player.get('playerId') == participant.get('api_id'):
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
    return {
      "error": "No matching data found"
    }
      
  except Exception:
    print_debug("Invalid participant data")
    return {
      "error": Exception,
      "message": "Invalid participant data"
    }

def parse_athlete_season_data(data, participant):
  try:
    athlete_season_data = data.get('league').get('players')[0].get('seasons')[0]
    
    return {
      'season': athlete_season_data.get('season'),
      'points': athlete_season_data.get('points'),
      'rebounds': athlete_season_data.get('rebounds'),
      'assists': athlete_season_data.get('assists'),
      'blocks': athlete_season_data.get('blocks'),
      'turnovers': athlete_season_data.get('turnovers')
    }
      
  except Exception:
    print_debug("Invalid participant data")
    return {
      "error": Exception,
      "message": "Invalid participant data"
    }

#Use this for printing
def print_debug(string):
    if(settings.DEBUG):
        print(string)