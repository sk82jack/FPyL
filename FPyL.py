import concurrent.futures
import csv
import requests

FPL_URL = "https://fantasy.premierleague.com/drf/"
GAMEWEEKS_SUMMARY_SUBURL = "events/"
PLAYERS_GAMEWEEK_SUBURL = "elements/"
TEAMS_GAMEWEEK_SUBURL = "teams/"
USER_SUMMARY_SUBURL = "element-summary/"
LEAGUE_CLASSIC_SUBURL = "leagues-classic-standings/"
LEAGUE_H2H_SUBURL = "leagues-h2h-standings/"
TEAM_ENTRY_SUBURL = "entry/"

GAMEWEEKS_SUMMARY_URL = FPL_URL + GAMEWEEKS_SUMMARY_SUBURL
PLAYERS_GAMEWEEK_URL = FPL_URL + PLAYERS_GAMEWEEK_SUBURL
TEAMS_GAMEWEEK_URL = FPL_URL + TEAMS_GAMEWEEK_SUBURL
USER_SUMMARY_URL = FPL_URL + USER_SUMMARY_SUBURL

def fpl_login(email_address, password):
    """Creates a requests session which logs you into the FPL website.

    Example:
        fpl_session = fpl_login('email_address', 'password')
        requests = fpl_session.get('https://fantasy.premierleague.com/drf/transfers').json()
    """
    fpl_session = requests.Session()
    url_home = 'https://users.premierleague.com/accounts/login/'
    fpl_session.get(url_home) # sets cookie
    csrftoken = fpl_session.cookies['csrftoken']
    values = {
        'csrfmiddlewaretoken': csrftoken,
        'login': email_address,
        'password': password,
        'app': 'plfpl-web',
        'redirect_uri': 'https://fantasy.premierleague.com/a/login'
    }
    fpl_session.post('https://users.premierleague.com/accounts/login/', data=values)
    return fpl_session

def get_current_gameweek():
    """Displays the current gameweek number"""
    response = requests.get(GAMEWEEKS_SUMMARY_URL).json()
    for gameweek in response:
        if gameweek['is_current']:
            return int(gameweek['id'])

def get_player_count():
    """Displays the total number of Fantasy Premier League players"""
    response = requests.get(PLAYERS_GAMEWEEK_URL).json()
    return int(len(response))

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

def get_gameweek_data(path):
    """Creates CSV file containing all data from the current gameweek"""
    gameweek = get_current_gameweek()
    my_week = []
    urls = []
    futures = []
    for i in range(get_player_count()):
        urls.append(USER_SUMMARY_URL + str(i + 1))
    pool = concurrent.futures.ThreadPoolExecutor(len(urls))
    for url in urls:
        futures.append(pool.submit(requests.get, url))
    for response in concurrent.futures.as_completed(futures):
        player = response.result().json()
        if player['history'][0]['round'] > gameweek:
            break

        for weeks in player['history']:
            if weeks['round'] == gameweek:
                my_week.append(weeks)

    filename = path + 'Week' + str(gameweek) + '.csv'

    this_week = open(filename, 'w')
    csvwriter = csv.writer(this_week, lineterminator='\n')
    count = 0
    for players in my_week:
        if count == 0:
            header = players.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(players.values())
    this_week.close()

def get_league_managers(league_id, league_type):
    """Get FPL managers in specified league

    Example: https://fantasy.premierleague.com/drf/leagues-classic-standings/336217?phase=1&le-page=1&ls-page=5
    """
    ls_page = 0
    managers = []
    if league_type == 'classic':
        league_type_suburl = LEAGUE_CLASSIC_SUBURL
    elif league_type == 'h2h':
        league_type_suburl = LEAGUE_H2H_SUBURL
    else:
        print("Please choose 'classic' or 'h2h' for league_type")
        return
    while True:
        ls_page += 1
        league_url = FPL_URL + league_type_suburl + str(league_id) + "?phase=1&le-page=1&ls-page=" + str(ls_page)
        response = requests.get(league_url).json()
        standings = response["standings"]
        for player in standings["results"]:
            team = {}
            team['Team'] = player['entry_name']
            team['Name'] = player['player_name']
            team['ID'] = player['entry']
            managers.append(team)
        if standings["has_next"] is False:
            break
    return managers

def get_manager_team(manager_id, gameweek_number):
    """Team picked by user.

    Example: https://fantasy.premierleague.com/drf/entry/2677936/event/1/picks
    """
    event_sub_url = "event/" + str(gameweek_number) + "/picks"
    team_gameweek_url = FPL_URL + TEAM_ENTRY_SUBURL + str(manager_id) + "/" + event_sub_url

    response = requests.get(team_gameweek_url).json()
    players = response["picks"]
    elements = []
    for player in players:
        elements.append(player["element"])
        if player["is_captain"]:
            captain_id = player["element"]

    return elements, captain_id
