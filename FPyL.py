from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import requests

FPL_URL = "https://fantasy.premierleague.com/drf/"
GAMEWEEKS_SUMMARY_SUBURL = "events/"
PLAYERS_GAMEWEEK_SUBURL = "elements/"
TEAMS_GAMEWEEK_SUBURL = "teams/"
USER_SUMMARY_SUBURL = "element-summary/"
LEAGUE_CLASSIC_STANDING_SUBURL = "leagues-classic-standings/"
LEAGUE_H2H_STANDING_SUBURL = "leagues-h2h-standings/"
TEAM_ENTRY_SUBURL = "entry/"

GAMEWEEKS_SUMMARY_URL = FPL_URL + GAMEWEEKS_SUMMARY_SUBURL
PLAYERS_GAMEWEEK_URL = FPL_URL + PLAYERS_GAMEWEEK_SUBURL
TEAMS_GAMEWEEK_URL = FPL_URL + TEAMS_GAMEWEEK_SUBURL
USER_SUMMARY_URL = FPL_URL + USER_SUMMARY_SUBURL

def get_current_gameweek():
    """Displays the current gameweek number"""
    response = requests.get(GAMEWEEKS_SUMMARY_URL).json()
    for gameweek in reversed(range(len(response))):
        while response[gameweek]["is_current"]:
            return int(response[gameweek]["id"])

def get_player_count():
    """Displays the total number of Fantasy Premier League players"""
    response = requests.get(PLAYERS_GAMEWEEK_URL).json()
    return int(len(response))

def fpl_login(username, password):
    """Creates a requests session which logs you into the FPL website."""
    with requests.Session() as fpl_session:
        values = {'csrfmiddlewaretoken': '##your token here##',
                  'login': username,
                  'password': password,
                  'app': 'plfpl-web',
                  'redirect_uri': 'https://fantasy.premierleague.com/a/login'}
        fpl_session.post('https://users.premierleague.com/accounts/login/', data=values)
    return fpl_session

def create_player_list():
    """creates JSON object of all player details with total scores,teams,positions etc."""
    response = requests.get(PLAYERS_GAMEWEEK_URL).json()
    return response

def get_teams():
    """Creates JSON object containing team names with ID numbers for matching data"""
    response = requests.get(TEAMS_GAMEWEEK_URL).json()
    teams = []

    for key in response:
        team = {}
        team['Name'] = key['name']
        team['ID'] = key['id']
        teams.append(team)
    return teams

def get_gameweek_data():
    """Creates CSV file containing all data from the current gameweek"""
    gameweek = get_current_gameweek()
    my_week = []
    urls = []
    futures = []
    for i in range(get_player_count()):
        urls.append(USER_SUMMARY_URL + str(i + 1))
    pool = ThreadPoolExecutor(len(urls))
    for url in urls:
        futures.append(pool.submit(urllib.urlopen, url))
    results = [r.result() for r in as_completed(futures)]
    for r in results:
        player = json.loads(r.read())
        if player['history'][0]['round'] > gameweek:
            break

        for weeks in player['history']:
            if weeks['round'] == gameweek:
                my_week.append(weeks)

    Filename = '##your filepath##\Week' + str(gameweek) + '.csv'

    ThisWeek = open(Filename, 'w')
    csvwriter = csv.writer(ThisWeek, lineterminator = '\n')
    count = 0
    for players in my_week:

        if count == 0:
            header = players.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(players.values())

    ThisWeek.close()
