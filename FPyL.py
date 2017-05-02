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
    """ Creates an authenticated requests session using FPL login credentials supplied.

        Example:
            fpl_session = fpl_login('email_address', 'password')
            response = json_response('https://fantasy.premierleague.com/drf/transfers')
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
    """ Get's the JSON response from an FPL URL with error checking.
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

def export_csv(json_data, file_name='CSV.csv'):
    """ Creates CSV file from JSON response and outputs to the CSV folder. You need to include the exntention in the filename

        Example:
            export_csv(top_1k(), 'Top 1K League Table.csv')

            This will create a CSV file called 'Top 1K League Table.csv' in the CSV folder.
            The default name is CSV.csv if not specified.
    """
    import csv

    filename = '.\\CSV\\' + file_name
    headers = json_data[0].keys()

    with open(filename, 'w', encoding='utf-16') as csv_file:
        csvwriter = csv.writer(csv_file, delimiter='\t', lineterminator='\n')
        csvwriter.writerow(headers)
        for row in json_data:
            csvwriter.writerow(row.values())

def current_gameweek():
    """ Outputs the current gameweek number as an integer
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

def player_ids():
    """ Creates 2 dictionaries; one of all the Premier League players and their player IDs and the other of all the Premier League players and their team IDs.
        The first dictionary is in the form {1: Hazard, 2: Kane, ...}
        The second dictionary is in the form {Hazard: 3, Kane: 10, ...}

        Example:
            players_id, players_team_id = player_ids()
            player = players_id[1]
            team_id = players_team_id['Hazard']
    """
    players = player_list()
    players_id = {}
    players_teamid = {}
    for player in players:
        players_id[player['id']] = player['web_name']
        players_teamid[player['web_name']] = player['team_code']
    return players_id, players_teamid

def team_ids():
    """ Creates a dictionary of all the Premier League teams and their IDs.
        The dictionary is in the form {1: Arsenal, 2: Bournemouth, ...}

        Example:
            teams = team_ids()
            team = teams[1]
    """
    response = json_response('https://fantasy.premierleague.com/drf/teams/')
    teams = {}
    for team in response:
        teams[team['code']] = team['name']
    return teams

def player_gameweek_history():
    """ Get player gameweek history
    """
    import concurrent.futures

    players = player_list()
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

def league_table(league_id, league_type):
    """ Get FPL league table in JSON format given a league ID and a league type.
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
            managers.append(player)
        if response['standings']['has_next'] is False:
            break
    return managers

def manager_team(manager_id, gameweek_number):
    """ Creates two outputs about a team picked in a previous gameweek by a specified manager on a specified gameweek.
    The first output is a list of player IDs for players in the team.
    The second output is the player ID of the captain for that gameweek.

        Example:
            players, captain = manager_team('30327','29')
            player_dict = player_ids()[0]
            team = []
            for player in players:
                if player == captain:
                    team.append(player_dict[player] + ' (C)')
                else:
                    team.append(player_dict[player])
            print(team)
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
    """ Get FPL league table in JSON format for the top 1000 players.
    """
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
