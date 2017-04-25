from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import requests

def get_current_gameweek():
    """Displays the current gameweek number"""
    url = "https://fantasy.premierleague.com/drf/events/"
    response = requests.get(url)
    json = response.json()
    for gameweek in reversed(range(len(json))):
        while json[gameweek]["is_current"]:
            return int(json[gameweek]["id"])

def get_player_count():
    """Displays the total number of Fantasy Premier League players"""
    url = "https://fantasy.premierleague.com/drf/elements/"
    response = requests.get(url)
    json = response.json()
    return int(len(json))

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
    url = "https://fantasy.premierleague.com/drf/elements/"
    response = requests.get(url)
    json = response.json()
    return json

def get_teams():
    """Creates JSON object containing team names with ID numbers for matching data"""
    url = "https://fantasy.premierleague.com/drf/teams/"
    response = requests.get(url)
    json = response.json()
    my_teams = []

    for i in range(len(json)):
        team = {}
        team['Name'] = json[i].get('name')
        team['ID'] = json[i].get('id')
        my_teams.append(team)
    return my_teams

def get_gameweek_data():
    """Creates CSV file containing all data from the current gameweek"""
    gameweek = get_current_gameweek()
    my_week = []
    urls = []
    futures = []
    for i in range(get_player_count()):
        urls.append("https://fantasy.premierleague.com/drf/element-summary/" + str(i + 1))
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