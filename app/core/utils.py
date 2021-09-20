
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

#Use this for printing
def print_debug(string):
    if(settings.DEBUG):
        print(string)