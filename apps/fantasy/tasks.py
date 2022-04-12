from datetime import datetime, timedelta
import decimal
import pytz
import xmltodict
import csv


from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files import File
from django.db.models import Q
from django.utils import timezone

from config import celery_app

from apps.fantasy import requests
from apps.fantasy.models import Athlete, Game, GameAthleteStat, GameTeam, Team
from apps.core import utils
from apps.core.svg import mbl_athlete_image, mbl_athlete_animation, mbl_athlete_animation_scipt

User = get_user_model()

athlete_ids = [10009104, 10001087, 10008455, 10003268, 10000040, 10001958, 10009269, 10008438, 10000029, 10007421, 10006276, 10006099, 10009865, 10001105, 10007068, 10009589, 10005913, 10005250, 10006790, 10000780, 10005445, 10001961, 10000689, 10006622, 10001133, 10006826, 10003340, 10000809, 10001862, 10005377, 10005480, 10005839, 10000981, 10007010, 10006953, 10008662, 10006969, 10007647, 10006492, 10006717, 10006354, 10007075, 10009032, 10001270, 10001261, 10007419, 10006518, 10006394, 10006417, 10006807, 10008608, 10000381, 10009500, 10008369, 10007008, 10001072, 10000249, 10000637, 10005751, 10005910, 10000164, 10000165, 10000177, 10000453, 10001896, 10007062, 10001940, 10003163, 10003298, 10001827, 10000839, 10001161, 10000837, 10008360, 10006571, 10007641, 10008525, 10002001, 10008694, 10005307, 10006046, 10007727, 10006940, 10000492, 10009344, 10000084, 10000343, 10009296, 10002113, 10001182, 10001305, 10003212, 10000151, 10005302, 10001207, 10002054, 10008206, 10000258, 10006462, 10006154, 10000633, 10008437, 10000261, 10000998, 10008721, 10010464, 10006960, 10003133, 10001154, 10005879, 10005654, 10005575, 10000469, 10007024, 10008325, 10009298, 10001945, 10000312, 10000534, 10006804, 10002075, 10007359, 10007121, 10006212, 10000686, 10007781, 10002115, 10007028, 10006353, 10007245, 10000060, 10007294, 10006718, 10006506, 10008190, 10006695, 10006611, 10006439, 10005586, 10001910, 10010180, 10000352, 10005878, 10006088, 10001926, 10005660, 10009350, 10007055, 10007106, 10009253, 10007061, 10006418, 10000405, 10000601, 10002076, 10003204, 10005353, 10006345, 10006371, 10006344, 10006157, 10006637, 10007070, 10007277, 10000440, 10005351, 10005352, 10005835, 10005998, 10006172, 10007115, 10006871, 10007011, 10000494, 10000213, 10005308, 10000133, 10000438, 10011494, 10000301, 10006614, 10001871, 10007675, 10005650, 10006112, 10000155, 10009262, 10010729, 10007048, 10000845, 10000485, 10000719, 10003328, 10005405, 10000357, 10005589, 10006007, 10000481, 10006868, 10007148, 10007152, 10009010, 10009354, 10009116, 10003360, 10000432, 10007637, 10008767, 10007231, 10010605, 10002013, 10007427, 10000525, 10000353, 10005530, 10002059, 10001369, 10009140, 10010332, 10001901, 10008618, 10009338, 10007589, 10000613, 10005970, 10006760, 10009274, 10005210, 10008667, 10000600, 10008984, 10001361, 10000484, 10007049, 10008331, 10001132, 10005922, 10000768, 10007604, 10006662, 10006893, 10006902, 10000805, 10008769, 10002061, 10007341, 10007263, 10008338, 10007085, 10000176, 10000041, 10000077, 10000640, 10001091, 10001955, 10002094, 10003122, 10003192, 10007125, 10007046, 10003314, 10001325, 10005607, 10000618, 10000555, 10002049, 10000364, 10007299, 10000225, 10006085, 10000270, 10005191, 10000346, 10005472, 10007153, 10000685, 10009327, 10001946, 10005534, 10009155, 10007256, 10005448, 10008537, 10008429, 10008679, 10007082, 10007151,
               10001179, 10005433, 10000691, 10001010, 10006841, 10002074, 10007200, 10000539, 10000082, 10001889, 10008980, 10008358, 10006837, 10007058, 10007041, 10006935, 10007274, 10005264, 10010721, 10005288, 10001934, 10001918, 10005493, 10000775, 10000779, 10000857, 10007040, 10003219, 10009300, 10006008, 10007050, 10008431, 10000886, 10000095, 10010317, 10010327, 10006850, 10001077, 10001907, 10001911, 10005542, 10005722, 10006033, 10000900, 10001009, 10001085, 10000437, 10000770, 10006775, 10007009, 10007367, 10000787, 10000330, 10000426, 10000880, 10012307, 10005249, 10000217, 10002087, 10001966, 10000690, 10001313, 10005406, 10000777, 10007554, 10007117, 10001865, 10000397, 10005476, 10007655, 10000970, 10000986, 10008677, 10006466, 10002077, 10007398, 10006195, 10006200, 10001264, 10007090, 10006682, 10001971, 10003376, 10008439, 10006535, 10007096, 10006568, 10005569, 10002091, 10000242, 10008483, 10007035, 10006118, 10002005, 10005787, 10002093, 10000675, 10000731, 10001365, 10000439, 10006124, 10000859, 10009271, 10009878, 10007287, 10002082, 10008357, 10007006, 10000807, 10005232, 10008281, 10000746, 10007228, 10006053, 10007765, 10007111, 10005309, 10002045, 10005366, 10000344, 10006867, 10006512, 10005919, 10005664, 10006540, 10006299, 10000247, 10009582, 10009636, 10007144, 10006198, 10007217, 10007203, 10005672, 10000129, 10007416, 10007562, 10000530, 10001053, 10001943, 10001271, 10007812, 10005633, 10003312, 10006242, 10000273, 10005368, 10001234, 10005311, 10005315, 10001248, 10004421, 10000215, 10001129, 10001130, 10001222, 10003177, 10000646, 10006977, 10009268, 10005773, 10001209, 10000813, 10000958, 10005772, 10006767, 10006907, 10001191, 10000284, 10000071, 10002099, 10007043, 10005680, 10006044, 10001947, 10006284, 10009303, 10000311, 10008490, 10005834, 10001939, 10009359, 10006863, 10007284, 10007135, 10000020, 10003325, 10007369, 10010374, 10009285, 10005822, 10008749, 10000031, 10003149, 10001166, 10000393, 10000406, 10005741, 10007017, 10005503, 10008529, 10006792, 10008292, 10012277, 10001162, 10001250, 10003259, 10007033, 10006945, 10008332, 10001902, 10008561, 10008373, 10006272, 10006421, 10006431, 10007224, 10008199, 10001086, 10005684, 10001083, 10005384, 10001225, 10008458, 10008477, 10006566, 10009346, 10008425, 10000335, 10006184, 10008743, 10000908, 10001979, 10002089, 10008989, 10009516, 10001088, 10000593, 10006136, 10005628, 10007553, 10000394, 10007126, 10008798, 10002058, 10001253, 10007025, 10007407, 10008318, 10000499, 10007013, 10007501, 10007259, 10006072, 10007244, 10007535, 10005661, 10001181, 10009628, 10001908, 10008834, 10007100, 10001993, 10000101, 10000628, 10010409, 10009612, 10007039, 10001350, 10003368, 10000955, 10006794, 10001094, 10005299, 10007310, 10007911, 10000529, 10000953, 10006634, 10008378, 10001127, 10006992, 10006805, 10000007, 10009288, 10005800, 10005808, 10000425]


@celery_app.task()
def update_mlb_team_scores():
    """Task for updating all mlb active games' teams scores per day"""

    # Task will run every 11:55 PM EST / 12:55 PM (next day) Manila time, so subtract -1 to day to get previous day since default timezone of Django is Asia/Manila
    date_query = timezone.now() - timedelta(days=1)
    date_query = date_query.strftime('%Y-%b-%d').upper()

    now = timezone.now()

    url = 'mlb/stats/json/PlayerGameStatsByDate/' + date_query

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
def update_mlb_athlete_stats():
    """Task for updating all athlete stats on the current season"""

    now = timezone.now()

    season = now.strftime('%Y').upper()
    # season = '2021'
    url = 'mlb/stats/json/PlayerSeasonStats/' + season

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

        if len(new_athlete_stats) > 0:
            GameAthleteStat.objects.bulk_create(new_athlete_stats, 20)
        if len(existing_athlete_stats) > 0:
            GameAthleteStat.objects.bulk_update(
                existing_athlete_stats,
                ['fantasy_score', 'singles', 'doubles', 'triples', 'home_runs',
                    'runs_batted_in', 'walks', 'hit_by_pitch', 'stolen_bases', 'position'],
                20
            )

        return(len(new_athlete_stats) + len(existing_athlete_stats))


@celery_app.task()
def sync_mlb_teams_data():
    """Task for syncing all teams data from sportsdata.io"""

    response = requests.get('mlb/scores/json/teams')

    print(response)

    if response['status'] == settings.RESPONSE['STATUS_OK']:
        teams_data = utils.parse_team_list_data(response['response'])

        for team in teams_data:
            Team.objects.update_or_create(
                api_id=team['api_id'],
                defaults={
                    'location': team['location'],
                    'name': team['name'],
                    'key': team['key'],
                    'sport': utils.SportType.MLB,
                    'primary_color': team['primary_color'],
                    'secondary_color': team['secondary_color']
                }
            )

        return len(teams_data)


@celery_app.task()
def sync_mlb_athletes_data():
    """Task for syncing all athlete data from sportsdata.io"""

    response = requests.get('mlb/scores/json/Players')

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

        return len(athlete_data)


@celery_app.task()
def init_mlb_athletes_data_csv():
    """Task for initializing all athlete data based on csv file"""
    with open('athletes.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0

        for row in csv_reader:
            api_id = row[0]
            first_name = row[9]
            last_name = row[10]
            position = row[7]
            salary = row[22]
            jersey = row[5]
            team_key = row[4]
            is_active = row[2]
            is_injured = row[31]

            if is_active == 'Active':
                is_active = True
            else:
                is_active = False

            if is_injured == 'null':
                is_injured = False
            else:
                is_injured = True

            if salary == 'null':
                salary = None

            if jersey == 'null':
                jersey = None

            team = Team.objects.get(key=team_key)

            Athlete.objects.update_or_create(
                api_id=api_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'position': position,
                    'salary': salary,
                    'jersey': jersey,
                    'is_active': is_active,
                    'is_injured': is_injured,
                    'team': team
                }
            )


@celery_app.task(soft_time_limit=99999999, time_limit=99999999)
def generate_athlete_images():
    output_dir = 'athlete_images/'
    file_extension = '.svg'

    athletes = Athlete.objects.all().order_by('pk')

    for athlete in athletes:
        athlete_id = str(athlete.id)

        file_name = output_dir + athlete_id + file_extension

        f = open(file_name, 'w')
        svg = mbl_athlete_image

        image_dict = xmltodict.parse(svg)

        jersey = '00'

        if athlete.jersey:
            jersey = str(athlete.jersey)

        # Change first name
        image_dict['svg']['g'][0]['text'][0]['#text'] = athlete.first_name.upper()
        # Change last name
        image_dict['svg']['g'][0]['text'][1]['#text'] = athlete.last_name.upper()
        # Change primary color
        image_dict['svg']['path'][10]['@style'] = 'fill: #' + athlete.team.primary_color  # 'fill: #000000'
        # Change secondary color
        image_dict['svg']['path'][9]['@style'] = 'fill: #' + athlete.team.secondary_color  # 'fill: #ffffff'
        # Change position
        image_dict['svg']['g'][0]['text'][2]['#text'] = athlete.position
        # Change jersey number
        image_dict['svg']['text']['#text'] = jersey

        image_xml = xmltodict.unparse(image_dict)

        f.write(image_xml)
        f.close()

        f = open(file_name, 'rb')

        file = File(f)
        athlete.nft_image.save(athlete_id + file_extension, file)

        f.close()


@celery_app.task(soft_time_limit=99999999, time_limit=99999999)
def generate_athlete_animations():
    output_dir = 'athlete_animations/'
    file_extension = '.svg'

    athletes = Athlete.objects.all().order_by('pk')

    for athlete in athletes:
        athlete_id = str(athlete.id)

        file_name = output_dir + athlete_id + file_extension

        f = open(file_name, 'w')

        base_animation = None
        base_image = None

        with open('mbl_base_image.svg', 'r') as file:
            base_image = file.read()

        with open('mbl_base_animation.svg', 'r') as file:
            base_animation = file.read()

        image_dict = xmltodict.parse(base_image)

        jersey = '00'

        if athlete.jersey:
            jersey = str(athlete.jersey)

        # Change first name
        image_dict['svg']['g'][4]['g'][3]['text'][0]['tspan']['#text'] = athlete.first_name.upper()
        image_dict['svg']['g'][4]['g'][3]['g']['text'][0]['tspan']['#text'] = athlete.first_name.upper()
        # # Change last name
        image_dict['svg']['g'][4]['g'][3]['text'][1]['tspan']['#text'] = athlete.last_name.upper()
        image_dict['svg']['g'][4]['g'][3]['g']['text'][1]['tspan']['#text'] = athlete.last_name.upper()
        # # Change primary color
        image_dict['svg']['g'][1]['g'][2]['g']['path']['@fill'] = '#' + athlete.team.primary_color
        # # Change secondary color
        image_dict['svg']['g'][1]['g'][0]['g']['path']['@fill'] = '#' + athlete.team.secondary_color
        # Change position
        image_dict['svg']['g'][4]['g'][2]['g']['text']['tspan']['#text'] = jersey
        # Change jersey number
        image_dict['svg']['g'][4]['g'][0]['g']['g']['text']['tspan']['#text'] = athlete.position

        image_xml = xmltodict.unparse(image_dict)

        style_end_tag = '</svg>'
        idx = image_xml.index(style_end_tag)
        image_xml = image_xml[:idx] + base_animation + image_xml[idx:]

        f.write(image_xml)
        f.close()

        f = open(file_name, 'rb')

        file = File(f)
        athlete.animation.save(athlete_id + file_extension, file)

        f.close()

        break


@ celery_app.task(soft_time_limit=99999999, time_limit=99999999)
def generate_jersey_images():
    output_dir = 'jersey_images/'
    file_extension = '.svg'

    athletes = Athlete.objects.filter(Q(api_id__in=athlete_ids))

    for athlete in athletes:
        athlete_id = str(athlete.id)

        file_name = output_dir + athlete_id + file_extension

        f = open(file_name, 'w')

        svg = """
            <svg id="Jersey_number" data-name="Jersey number" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 99.37 89.14">
                <defs>
                    <style type="text/css">@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,700;1,700');</style>
                    <style>
                    .cls-1 {
                        font-size: 69.37px;
                        fill: #fff;
                        font-family: Montserrat-BoldItalic, Montserrat;
                        font-weight: 700;
                        font-style: italic;
                    }
                    </style>
                </defs>
                <text class="cls-1" transform="translate(10.07 71.15) rotate(-8.42)">27</text>
            </svg>
        """

        image_dict = xmltodict.parse(svg)

        jersey = '00'

        if athlete.jersey:
            jersey = str(athlete.jersey)

        image_dict['svg']['text']['#text'] = jersey

        image_xml = xmltodict.unparse(image_dict)

        f.write(image_xml)
        f.close()

        f = open(file_name, 'rb')

        file = File(f)
        athlete.jersey_image.save(athlete_id + file_extension, file)

        f.close()


@ celery_app.task(soft_time_limit=99999999, time_limit=99999999)
def generate_name_images():
    output_dir = 'name_images/'
    file_extension = '.svg'

    athletes = Athlete.objects.filter(Q(api_id__in=athlete_ids))

    for athlete in athletes:
        athlete_id = str(athlete.id)

        file_name = output_dir + athlete_id + file_extension

        f = open(file_name, 'w')

        svg = """
           <svg id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 34.16 27.35">
                <defs>
                    <style type="text/css">@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,700;1,700');</style>
                    <style>
                    .cls-1 {
                        font-size: 7px;
                        fill: #fff;
                        font-family: Montserrat-BoldItalic, Montserrat;
                        font-weight: 700;
                        font-style: italic;
                    }

                    .cls-2 {
                        letter-spacing: -0.01em;
                    }
                    </style>
                </defs>
                <text class="cls-1" transform="translate(1.88 11.15) rotate(-8.42)">MIKE</text>
                <text class="cls-1" transform="translate(1.12 25.05) rotate(-8.42)">TROUT</text>
            </svg>
        """

        image_dict = xmltodict.parse(svg)

        # Change first name
        image_dict['svg']['text'][0]['#text'] = athlete.first_name.upper()
        # Change last name
        image_dict['svg']['text'][1]['#text'] = athlete.last_name.upper()

        image_xml = xmltodict.unparse(image_dict)

        f.write(image_xml)
        f.close()

        f = open(file_name, 'rb')

        file = File(f)
        athlete.name_image.save(athlete_id + file_extension, file)

        f.close()


@ celery_app.task(soft_time_limit=99999999, time_limit=99999999)
def generate_position_images():
    output_dir = 'position_images/'
    file_extension = '.svg'

    athletes = Athlete.objects.filter(Q(api_id__in=athlete_ids))

    for athlete in athletes:
        athlete_id = str(athlete.id)

        file_name = output_dir + athlete_id + file_extension

        f = open(file_name, 'w')

        svg = """
            <svg id="Layer_1" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 15.78 16.8">
                <defs>
                    <style type="text/css">@import url('https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,700;1,700');</style>
                    <style>
                    .cls-1 {
                        font-size: 8px;
                        font-family: Montserrat-BoldItalic, Montserrat;
                        font-weight: 700;
                        font-style: italic;
                    }

                    .cls-1, .cls-2 {
                        fill: #fff;
                    }
                    </style>
                </defs>
                <text class="cls-1" transform="translate(1.24 14.23) rotate(-8.42)">CF</text>
                <polygon class="cls-2" points="1.7 1.28 1.7 2.31 10.13 1.04 10.13 0 1.7 1.28"/>
            </svg>
        """

        image_dict = xmltodict.parse(svg)

        image_dict['svg']['text']['#text'] = athlete.position.upper()

        image_xml = xmltodict.unparse(image_dict)

        f.write(image_xml)
        f.close()

        f = open(file_name, 'rb')

        file = File(f)
        athlete.position_image.save(athlete_id + file_extension, file)

        f.close()
