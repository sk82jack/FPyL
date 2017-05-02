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

def fpl_login(email_address, password):
    """ Creates a requests session which logs you into the FPL website.

        Example:
            fpl_session = fpl_login('email_address', 'password')
            requests = fpl_session.get('https://fantasy.premierleague.com/drf/transfers').json()
    """
    import requests

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

def json_response(url, session=''):
    """ Get's the JSON response from a specified URL with error checking.
    """
    import requests
    if session == '':
        fpl_session = requests.session()
    else:
        fpl_session = session
    try:
        return fpl_session.get(url).json()
    except ValueError:
        import sys
        def excepthook(type, value, traceback):
            print(value)
        sys.excepthook = excepthook
        raise ValueError('The game is currently being updated. Please try again later.')

def export_csv(json_data, name='CSV'):
    """ Creates CSV file from JSON response
    """
    import csv

    filename = '.\\CSV\\' + name + '.csv'
    headers = json_data[0].keys()

    with open(filename, 'w', encoding='utf-16') as csv_file:
        csvwriter = csv.writer(csv_file, delimiter='\t', lineterminator='\n')
        csvwriter.writerow(headers)
        for row in json_data:
            csvwriter.writerow(row.values())

def current_gameweek():
    """ Displays the current gameweek number
    """
    response = json_response('https://fantasy.premierleague.com/drf/events/')
    for gameweek in response:
        if gameweek['is_current']:
            return gameweek['id']

def player_list():
    """ creates JSON object of all player details with total scores,teams,positions etc.
    """
    response = json_response('https://fantasy.premierleague.com/drf/elements/')
    return response

def teams():
    """ Creates JSON object containing team names with ID numbers for matching data
    """
    response = json_response('https://fantasy.premierleague.com/drf/teams/')
    return response

def player_data_history():
    """ Get player data history
    """
    import concurrent.futures

    players = json_response('https://fantasy.premierleague.com/drf/elements/')
    player_data = []
    urls = []
    # Generate list of URLs to iterate over
    for i in range(len(players)):
        url = 'https://fantasy.premierleague.com/drf/element-summary/' + str(i+1)
        urls.append(url)

    # Retrieve the player data
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = [executor.submit(json_response, url) for url in urls]
        for future in concurrent.futures.as_completed(future_to_url):
            for player in future.result()['history']:
                player_data.append(player)
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
        league_url = 'https://fantasy.premierleague.com/drf/' + suburl + str(league_id) + '?phase=1&le-page=1&ls-page=' + str(ls_page)
        response = json_response(league_url)
        for player in response['standings']["results"]:
            managers.append({
                'team': player['entry_name'],
                'Name': player['player_name'],
                'ID': player['entry']
                })
        if response['standings']['has_next'] is False:
            break
    return managers

def manager_team(manager_id, gameweek_number):
    """ Team picked by user.

        Example: https://fantasy.premierleague.com/drf/entry/2677936/event/1/picks
    """
    team_gameweek_url = 'https://fantasy.premierleague.com/drf/entry/' + str(manager_id) + '/event/' + str(gameweek_number) + '/picks'
    response = json_response(team_gameweek_url)
    elements = []
    for player in response['picks']:
        elements.append(player['element'])
        if player['is_captain']:
            captain_id = player['element']
    return elements, captain_id

def top_1k():
    import concurrent.futures
    suburl = 'https://fantasy.premierleague.com/drf/leagues-classic-standings/313?phase=1&le-page=1&ls-page='
    urls = []
    top_1k_teams = []
    for ls_page in range(1, 21):
        urls.append(suburl + str(ls_page))
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_url = [executor.submit(json_response, url) for url in urls]
        for future in concurrent.futures.as_completed(future_to_url):
            for team in future.result()['standings']['results']:
                top_1k_teams.append(team)
    return top_1k_teams
