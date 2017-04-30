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

def json_response(url):
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

def export_csv(json_data, name="CSV"):
    """ Creates CSV file from JSON response
    """
    filename = '.\\CSV\\' + name + '.csv'

    this_week = open(filename, 'w')
    csvwriter = csv.writer(this_week, lineterminator='\n')
    count = 0
    for row in json_data:
        if count == 0:
            header = row.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(row.values())
    this_week.close()

def current_gameweek():
    """ Displays the current gameweek number
    """
    response = json_response(FPL_URL + 'events/')
    for gameweek in response:
        if gameweek['is_current']:
            return gameweek['id']

def player_list():
    """ creates JSON object of all player details with total scores,teams,positions etc.
    """
    response = json_response(FPL_URL + 'elements/')
    return response

def teams():
    """ Creates JSON object containing team names with ID numbers for matching data
    """
    response = json_response(FPL_URL + 'teams/')
    teams_info = [{'name': key['name'], 'id': key['id']} for key in response]
    return teams_info

def player_data_history():
    """ Get player data history
    """
    players = requests.get(FPL_URL + 'elements/').json()
    player_data = []
    urls = []
    # Generate list of URLs to iterate over
    for i in range(len(players)):
        url = FPL_URL + 'element-summary/' + str(i+1)
        urls.append(url)

    # Retrieve the player data
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = [executor.submit(json_response, url) for url in urls]
        for future in concurrent.futures.as_completed(future_to_url):
            player_data.append(future.result()['history'])
    return player_data

def league_managers(league_id, league_type):
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
        league_url = FPL_URL + suburl + str(league_id) + '?phase=1&le-page=1&ls-page=' + str(ls_page)
        response = json_response(league_url)
        managers = [{
            'team': player['entry_name'],
            'Name': player['player_name'],
            'ID': player['entry']
            } for player in response['standings']["results"]]
        if response['standings']['has_next'] is False:
            break
    return managers

def manager_team(manager_id, gameweek_number):
    """ Team picked by user.

        Example: https://fantasy.premierleague.com/drf/entry/2677936/event/1/picks
    """
    team_gameweek_url = FPL_URL + 'entry/' + str(manager_id) + '/event/' + str(gameweek_number) + '/picks'
    response = json_response(team_gameweek_url)
    elements = []
    for player in response['picks']:
        elements.append(player['element'])
        if player['is_captain']:
            captain_id = player['element']
    return elements, captain_id
