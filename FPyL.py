import json
import urllib
import csv
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

#gets current gameweek number
def GetCurrentGameweek():
    url = "https://fantasy.premierleague.com/drf/events/"
    response = urllib.urlopen(url)
    gameweek = json.loads(response.read())
    for weeks in range(len(gameweek)):
        while gameweek[weeks]["is_current"]:
            return gameweek[weeks]["id"]
            break

#gets count of current active FPL players
def GetPlayerCount():
    url = "https://fantasy.premierleague.com/drf/elements/"
    response = urllib.urlopen(url)
    players = json.loads(response.read())
    return len(players)
    
#creates a requests session which logs you into the FPL website. use for any code where you need to log in to retreieve data
def FPLlogin():
    with requests.Session() as session:
            values = {'csrfmiddlewaretoken': '##your token here##',
                      'login': '##fpl login email##',
                      'password': '##fpl login password##',
                      'app': 'plfpl-web',
                      'redirect_uri': 'https://fantasy.premierleague.com/a/login'}
            session.post('https://users.premierleague.com/accounts/login/',data = values)
    return session
   
#creates JSON object of all player details with total scores,teams,positions etc.
def CreatePlayerList():
    response = urllib.urlopen("https://fantasy.premierleague.com/drf/elements/")
    PlayerList = json.loads(response.read(),)
    return PlayerList

#Creates JSON object containing team names with ID numbers for matching data
def GetTeams():
    response = urllib.urlopen('https://fantasy.premierleague.com/drf/teams/')
    Teams = json.loads(response.read(),)
    MyTeams = []

    for i in range(len(Teams)):
        TeamEdit = {}
        TeamEdit['Name'] = Teams[i].get('name')
        TeamEdit['ID'] = Teams[i].get('id')
        MyTeams.append(TeamEdit)
    return MyTeams


#creates CSV file containing all data from the current gameweek
def GetGameweekData():    
    gw = GetCurrentGameweek() 
    MyWeek = []      
    urls = ["https://fantasy.premierleague.com/drf/element-summary/" + str(i + 1) for i in range(GetPlayerCount())]
    pool = ThreadPoolExecutor(len(urls))
    futures = [pool.submit(urllib.urlopen,url) for url in urls]
    results = [r.result() for r in as_completed(futures)]
    for r in results:
        player = json.loads(r.read())
        
        if player['history'][0]['round'] >  gw:
                break

        for weeks in player['history']:
            if weeks['round'] == gw:
                MyWeek.append(weeks)
    
    Filename ='##your filepath##\Week' + str(gw) + '.csv'

    ThisWeek = open(Filename, 'w')
    csvwriter = csv.writer(ThisWeek,lineterminator = '\n')
    count = 0
    for players in MyWeek:

        if count == 0:
            header = players.keys()
            csvwriter.writerow(header)
            count += 1
        csvwriter.writerow(players.values())

    ThisWeek.close()

    
