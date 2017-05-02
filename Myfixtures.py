import argparse
import colorama
import FPyL
import terminaltables

colorama.init()

parser = argparse.ArgumentParser(description='Get upcoming fixtures for your players')
parser.add_argument('-e', '--email', help='FPL email address', required = True)
parser.add_argument('-p', '--password', help='FPL password', required = True)
args = parser.parse_args()

result = []
fpl_session = FPyL.fpl_login(args.email, args.password)
teams = FPyL.teams_ids()

# Get users team info
response = FPyL.json_response(url='https://fantasy.premierleague.com/drf/transfers', session=fpl_session)
fpl_session.close()
player_ids = [player['element'] for player in response['picks']]
for player_id in player_ids:
    # Get player names from the IDs
    for player in FPyL.json_response('https://fantasy.premierleague.com/drf/elements/'):
        if player['id'] == player_id:
            name = player['web_name']
            team_code = player['team_code']
    team_name = teams[team_code]
    # Create the player dictionary
    temp_player = {
        'id': player_id,
        'name': name + '\n(' + team_name + ')'
    }
    # Get future fixtures info
    fixtures = FPyL.json_response('https://fantasy.premierleague.com/drf/element-summary/' + str(player_id))['fixtures']
    for fixture in fixtures:
        if fixture['difficulty'] <= 2:
            opponent = colorama.Fore.GREEN + fixture['opponent_name'] + colorama.Style.RESET_ALL
        elif fixture['difficulty'] <= 3:
            opponent = colorama.Fore.YELLOW + fixture['opponent_name'] + colorama.Style.RESET_ALL
        else:
            opponent = colorama.Fore.RED + fixture['opponent_name'] + colorama.Style.RESET_ALL
        if fixture['event_name'] not in temp_player:
            temp_player[fixture['event_name']] = opponent
        else:
            temp_player[fixture['event_name']] = temp_player[fixture['event_name']] + '\n' + opponent
    result.append(temp_player)
headers = ['Player']
# Get the upcoming gameweek
gw = response['entry']['current_event'] + 1
max_gw = gw + 5
while (gw <= 38) and (gw <= max_gw):
    headers.append('Gameweek ' + str(gw))
    gw += 1
data = []
data.append(headers)
for player in result:
    row = []
    row.append(player['name'])
    for gameweek in headers[1:]:
        row.append(player[gameweek])
    data.append(row)

table = terminaltables.SingleTable(data, title=colorama.Back.WHITE + colorama.Fore.BLACK + 'Upcoming Fixtures' + colorama.Style.RESET_ALL)
table.inner_row_border = True
for i in range(len(headers)):
    table.justify_columns[i] = 'center'
print(table.table)
