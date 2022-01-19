import sys
import requests

HEADERS = {"Content-Type": "application/json"}
BASE_URL = "https://api.playible.io/"


def main(game_id):
    url = BASE_URL + "fantasy/game/" + game_id + "/leaderboard"
    result = requests.request(
        "GET", (url)
    )
    json_result = result.json()
    return json_result


if __name__ == "__main__":
    try:
        print(main(*sys.argv[1:]))
    except Exception as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
