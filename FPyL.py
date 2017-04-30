import concurrent.futures
import csv
import requests

### Relative links:
###
### bootstrap ---------------------------- (more data if authenticated)
### bootstrap-static ---------------------
### bootstrap-dynamic --------------------
### events -------------------------------
### elements -----------------------------
### element-summary ----------------------
### element-types ------------------------
### fixtures -----------------------------
### teams --------------------------------
### region -------------------------------
### entry/{entryId} ----------------------
### transfers ---------------------------- (requires auth)
### my-team/{teamId} --------------------- (requires auth)
### leagues-entered/{teamId} ------------- (requires auth)
### leagues-classic-standings/{leagueId} -
### leagues-h2h-standings/{leagueId} -----
### leagues-classic/{leagueId} ----------- (must be a member)
### leagues-h2h/{leagueId} --------------- (must be a member)

FPL_URL = 'https://fantasy.premierleague.com/drf/'

def fpl_login(email_address, password):
    """ Creates a requests session which logs you into the FPL website.

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
    fpl_session.post(url_home, data=values)
    return fpl_session

def get_json_response(url):
    """ Get's the JSON response from a specified URL with error checking.
    """
    with requests.session() as session:
        try:
            return session.get(url).json()
        except ValueError:
            import sys
            def excepthook(type, value, traceback):
                print(value)
            sys.excepthook = excepthook
            raise ValueError('The game is currently being updated. Please try again later.')

def get_current_gameweek():
    """ Displays the current gameweek number
    """
    response = get_json_response(FPL_URL+'events/')
    for gameweek in response:
        if gameweek['is_current']:
            return gameweek['id']

def get_player_list():
    """ creates JSON object of all player details with total scores,teams,positions etc.
    """
    response = get_json_response(FPL_URL+'elements/')
    return response

def get_teams():
    """ Creates JSON object containing team names with ID numbers for matching data
    """
    response = get_json_response(TEAMS_GAMEWEEK_URL)
    teams = [{'name': key['name'], 'id': key['id']} for key in response]
    return teams

def get_gameweek_data(path):
    """ Creates CSV file containing all data from the current gameweek
    """
    gameweek = get_current_gameweek()
    my_week = []
    urls = [FPL_URL+'element-summary/'+str(i + 1) for i in range(len(get_player_list()))]
    pool = concurrent.futures.ThreadPoolExecutor(len(urls))
    futures = [pool.submit(get_json_response, url) for url in urls]
    for response in concurrent.futures.as_completed(futures):
        player = response.result()
        if player['history'][0]['round'] > gameweek:
            break
        for weeks in player['history']:
            if weeks['round'] == gameweek:
                my_week.append(weeks)

    filename = ''.join([path, 'Week', str(gameweek), '.csv'])

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
    """ Get FPL managers in specified league

        Example: https://fantasy.premierleague.com/drf/leagues-classic-standings/336217?phase=1&le-page=1&ls-page=5
    """
    ls_page = 0
    managers = []
    if league_type == 'classic':
        suburl = 'leagues-classic-standings/'
    elif league_type == 'h2h':
        suburl = 'leagues-h2h-standings/'
    else:
        print('Please choose \'classic\' or \'h2h\' for league_type')
        return
    while True:
        ls_page += 1
        league_url = FPL_URL+suburl+str(league_id)+'?phase=1&le-page=1&ls-page='+str(ls_page)
        response = get_json_response(league_url)
        managers = [{
            'team': player['entry_name'],
            'Name': player['player_name'],
            'ID': player['entry']
            } for player in response['standings']["results"]]
        if response['standings']['has_next'] is False:
            break
    return managers

def get_manager_team(manager_id, gameweek_number):
    """ Team picked by user.

        Example: https://fantasy.premierleague.com/drf/entry/2677936/event/1/picks
    """
    team_gameweek_url = FPL_URL+'entry/'+str(manager_id)+'/event/'+str(gameweek_number)+'/picks'
    response = get_json_response(team_gameweek_url)
    elements = []
    for player in response['picks']:
        elements.append(player['element'])
        if player['is_captain']:
            captain_id = player['element']
    return elements, captain_id
