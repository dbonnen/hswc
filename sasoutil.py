#!/usr/bin/python

import sqlite3, sys, re
#dbconn = sqlite3.connect('hswc.db')

## Assumptions about the database are currently:

#sqlite> .schema
#CREATE TABLE pending(dwname TEXT, email TEXT, team_type TEXT, team TEXT, fandom TEXT, cpn_willing BIT, notes TEXT, extrafield TEXT);
#CREATE TABLE players(dwname TEXT PRIMARY KEY, team_id INT, email TEXT, tumblr TEXT, twitter TEXT, cpn_willing BIT, cpn BIT, vice_captain BIT, notes TEXT, extrafield TEXT);
#CREATE TABLE teams(team_id INT PRIMARY KEY, team_name TEXT, team_type TEXT, fandom TEXT, num_participants INT, captain TEXT, vice_captain TEXT, active BIT, total_score INT, mr1 INT, mr2 INT, br0 INT, br1 INT, br2 INT, br3 INT, br4 INT, br5 INT, br6 INT, penalty INT, comm_name TEXT, extrafield TEXT);

## this is minorly belunkus but it's a starting point at least
## in particular the players table doesn't need 'flwilling'
## and having it be dwname and name in different tables is _kind_ of
## stupid although also a reminder of which table you're working with

## extrafield is there in case I forgot something and need to insert it 
## in the middle of the event, which is probably the sort of thing you 
## only do when you are writing hackity nonsense for shipping competitions, 
## but that's what I'm doing so here we are

#cursor = dbconn.cursor()

def send_inactives_to_grandstand(cursor):
    """Take players on inactive teams and send them to grandstand."""
    ##UPDATE FOR SASO, TEAM SETUP IS A LITTLE DIFFERENT
    ##MAYBE MAKE A SWITCH TEAM FUNCTION?
    allteams = get_list_of_teams(cursor)
    
    for team in allteams:
        if not is_team_active(team, cursor):
            players = get_team_members_list(team, cursor)
            for player in players:
                add_player_to_grandstand(player, cursor)
                remove_player_from_team(player, team, cursor)
    
    #dbconn.commit()
    return

def make_cpn_list(cursor):
    """Make a list of all teams, their captains, and their email addresses."""
    #FINISHED FOR SASO
    cursor.execute('SELECT * from teams where active=1')
    allteams = cursor.fetchall()
    bakedteams = []
    
    for team in allteams:
        if not team[5]:
            teamtuple = (team[1], 'none', 'none')
        else:
            cpn = team[5]
            email = get_player_email(cpn, cursor)
            teamtuple = (team[1], cpn, email)
        bakedteams.append(teamtuple)
    
    return bakedteams

def get_player_email(player, cursor):
    """Get a player's email address."""
    #FINISHED FOR SASO
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    playerdata = cursor.fetchone()
    if not playerdata:
        return "player does not exist"
    return playerdata[2]

def make_team_active(team, cursor):
    """Set the active bit on a team."""
    #FINISHED FOR SASO
    string = """UPDATE teams set active=1 where name='%s'""" % team
    cursor.execute(string)
    # whatever calls this has to dbconn.commit()
    return

def is_team_active(team, cursor):
    """Return the active bit on a team."""
    #FINISHED FOR SASO
    if team == 'grandstand':
        return 'yes'
    
    array = (team,)
    cursor.execute('SELECT * from teams where name=?', array)
    thing = cursor.fetchone()
    if thing:
        activebit = thing[7]
        return activebit
    # team does not exist
    return

def activate_qualifying_teams(cursor):
    """Set the active bit on all teams with 4 or more participants.
    And all teams that are abstrata."""
    #FINISHED FOR SASO

    teamlist = get_list_of_teams(cursor)
    for team in teamlist:
        count = get_team_members_count(team, cursor)
        if count >= 4:
            make_team_active(team, cursor)
    return

def make_pending_entry(dwname, email, team, captain, notes, team_type, fandom, cursor):
    """Make a pending entry to be processed if the DW auth goes through."""
    #FINISHED FOR SASO
    array = (dwname, email, team_type, team, fandom, captain, notes)
    cursor.execute('INSERT into pending (dwname, email, team_type, team, fandom, cpn_willing, notes) values (?,?,?,?,?,?,?)', array)
    return

def retrieve_pending_entry(dwname, cursor):
    """Get a pending entry out for a username."""
    #FINISHED FOR SASO
    array = (dwname,)
    cursor.execute('SELECT * from pending where dwname=?', array)
    pending_entry = cursor.fetchone()
    return pending_entry

def remove_pending_entry(dwname, cursor):
    """Remove a pending entry for a username."""
    #FINISHED FOR SASO
    array = (dwname,)
    cursor.execute('DELETE from pending where dwname=?', array)
    #dbconn.commit()
    return

def team_exists(teamname, cursor):
    """See if a team exists in the database or not. If yes, return 1,
      if not return 0."""
    #FINISHED FOR SASO
    array = (teamname,) # for sanitizing
    if teamname == 'grandstand':
        return 1
    cursor.execute('SELECT * from teams where team_name=?', array)
    if cursor.fetchone():
        return 1 
    else:
        return 0 

def team_has_captain(teamname, cursor):
    """If a team has a friendleader, return 0, otherwise return 1"""
    #FINISHED FOR SASO
    array = (teamname,)
    if not team_exists(teamname, cursor):
        # there's not a friendleader if there's no team!
        return 0
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamlist = cursor.fetchone()
    if teamlist[5]:
        return 1
    else:
        return 0

def player_exists(player, cursor):
    """See if a player exists in the database or not. If yes, return 1,
       if not return 0."""
    #FINISHED FOR SASO
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    if cursor.fetchone():
        return 1
    else:
        return 0

def get_current_team(player, cursor):
    """Get the team the player is currently on, if there is one."""
    #FINISHED FOR SASO
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    currentteam = cursor.fetchone()
    if currentteam:
        cursor.execute('SELECT * from teams where team_id=?', (currentteam[2],))
        realteam = cursor.fetchone()
        if realteam:
            return realteam[1]
    else:
        return 0
    
def add_team(teamname, teamtype, fandom, cursor):
    """Add a team to the database."""
    #UPDATED, MAY NEED FURTHER UPDATING
    id_no = get_newest_team(cursor) + 1
    array = (id_no, teamname, teamtype, fandom, 0, '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    cursor.execute('INSERT into teams (team_id, team_name, team_type, fandom, num_participants, captain, active, total_score, mr1, mr2, br0, br1, br2, br3, br4, br5, br6, penalty) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', array)
    #dbconn.commit()
    return

def remove_team(teamname, cursor):
    """Delete a team."""
    #FINISHED FOR SASO
    array = (teamname,)
    if teamname == 'grandstand':
        # don't delete grandstand
        return
    cursor.execute('DELETE from teams where team_name=?', array)
    #dbconn.commit()
    return

def remove_player(player, cursor):
    """Delete a player."""
    #FINISHED FOR SASO
    array = (player,)
    cursor.execute('DELETE from players where dwname=?', array)
    #dbconn.commit()
    return

def get_list_of_teams(cursor):
    """Get a list of all teams."""
    #FINISHED FOR SASO
    teamlist = []
    for team in cursor.execute('SELECT * from teams'):
        teamlist.append(team[1]) # man isn't it cool that order matters
    # soni doesn't like it alphabetical
    # teamlist.sort()
    return teamlist

def get_teamcount(cursor):
    """Get a count of teams."""
    #FINISHED FOR SASO
    teamlist = get_list_of_teams(cursor)
    return len(teamlist)

def get_playercount(cursor):
    """Get a count of players."""
    #FINISHED FOR SASO
    playerlist = []
    for player in cursor.execute('SELECT * from players'):
        playerlist.append(player[0])
    return len(playerlist)

def get_captain(team, cursor):
    """Get the captain of a team, if one exists."""
    #FINISHED FOR SASO
    array = (team, )
    if not team_exists(team, cursor):
        return 0
    if team == 'grandstand':
        return 'olympics-mods'
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamrow = cursor.fetchone()
    return teamrow[5]

def make_captain(player, teamname, cursor):
    """Make player captain of teamname."""
    #FINISHED FOR SASO
    array = (player, teamname)
    cursor.execute('UPDATE teams set captain=? where name=?', array) 
    cursor.execute('UPDATE players set cpn=? where name=?', (1, player))
    #cursor.execute('UPDATE players set captain=? where dwname=?', ('yes', player))
    #dbconn.commit()
    return

def remove_player_from_grandstand(player, cursor):
    """Remove a player from grandstand."""
    #FINISHED FOR SASO
    array = (player,)
    #cursor.execute('DELETE from grandstand where dwname=?', array)
    #dbconn.commit()
    cursor.execute('UPDATE players set team_id=-1 where dwname=?', array)
    cursor.execute('UPDATE teams set num_participants = (num_participants-1) where team_id=0')
    return

def add_player_to_grandstand(player, cursor):
    """Add a player to grandstand."""
    #FINISHED FOR SASO
    array = (player,)
    #cursor.execute('INSERT into grandstand (dwname) values (?)', array)
    cursor.execute('UPDATE players set team_id=? where dwname=?', (0, player))
    cursor.execute('UPDATE teams set num_participants = (num_participants + 1) where team_id=0')
    return

def remove_player_from_team(player, teamname, cursor):
    """Remove a player from a team, presumably because they joined another."""
    #FINISHED FOR SASO
    array = (teamname,)
    if teamname == 'grandstand':
        remove_player_from_grandstand(player, cursor)
        return
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamdatalist = cursor.fetchone()
    if teamdatalist[5] == player:
        cursor.execute('UPDATE teams set captain=? where team_id=?', ('',teamdatalist[0]))
        cursor.execute('UPDATE players set cpn=0 where dwname=?', (player))
    if teamdatalist[6] == player:
        cursor.execute('UPDATE teams set vice_captain=? where team_id=?', ('', teamdatalist[0]))
        cursor.execute('UPDATE players set vice_captain=0 where dwname=?', (player))
    cursor.execute('UPDATE teams set num_participants = (num_participants - 1) where team_id=?', (teamdatalist[0]))
    cursor.execute('UPDATE players set team_id= -1 where dwname=?', (player))
    #dbconn.commit()
    return

def update_player(player, email, notes, cursor):
    """Update the player's information in the db after a new form submission."""
    #team does not change
    #FINISHED FOR SASO
    array=(email, notes, teamname, player)
    cursor.execute('UPDATE players set email=?, notes=?, team=? where dwname=?', array)
    #dbconn.commit()
    return

def add_player_to_players(player, email, cpnwilling, notes, cursor):
    """Put the player in the player database at all.
       Team preference is not handled here."""
    #FINISHED FOR SASO
    array=(player, -1, cpnwilling, email, notes)
    cursor.execute('INSERT into players (dwname, team_id, cpn_willing, email, notes) values (?,?,?,?,?)', array)
    #dbconn.commit()
    return

def get_team_members_count(team, cursor):
    """How many players on the team?"""
    #FINISHED FOR SASO
    array=(team,)
    if not team_exists(team, cursor):
        return 0
    cursor.execute('SELECT * from teams where team_name=?',array)
    team_info = cursor.fetchone()
    return team_info[4]

def get_team_members_list(team, cursor):
    """Who are the players on the team?"""
    #FINISHED FOR SASO
    array = (team,)
    if not team_exists(team, cursor):
        return 0
    cursor.execute('SELECT * from teams where name=?', array)
    teamdatalist = cursor.fetchone()
    team_id = teamdatalist[0]
    teamplayers = []
    for x in cursor.execute('SELECT * from players where team_id=?', (team_id,)):
        teamplayers.append(x[0])
    return teamplayers

'''def get_grandstand_members_count(cursor):
    """How many players on team grandstand?"""
    cursor.execute('SELECT * from grandstand')
    grandstandlist = cursor.fetchall()
    return len(grandstandlist)


def get_grandstand_members_list(cursor):
    """Which players are on team grandstand?"""
    cursor.execute('SELECT * from grandstand')
    grandstandlist = cursor.fetchall()
    if not grandstandlist:
        return ['nobody']
    grandstandplayers = []
    for x in grandstandlist:
        grandstandplayers.append(x[0])
    grandstandplayers.sort()
    return grandstandplayers
'''
#the schema of our database renders these functions unnecessary

def player_is_on_team(player, team, cursor):
    """Is the player on the team?"""
    #FINISHED FOR SASO
    array=(team,)
    if not team_exists(team, cursor):
        return 0
    cursor.execute('SELECT * from teams where team_name=?',array)
    teamdatalist = cursor.fetchone()
    team_team_id = teamdatalist[0]
    cursor.execute('SELECT * from players where dwname=?', (player,))
    playerlist = cursor.fetchone()
    player_team_id = playerlist[1]
    if team_team_id == player_team_id:
        return 1
    return 0

def get_team_display_line(team, cursor):
    """Make the display line that goes into the teams table.
    Format is csstype, count, teamname, fl, stringofallplayers."""
    #FIX UP LATER, ONCE I GET /SASO/GRANDSTAND WORKING...
    array=(team,)
    teamname = re.sub('<', '&lt;', team)
    teamname = re.sub('>', '&gt;', teamname)
    if teamname == 'grandstand':
        stringofallplayers = 'Please see the grandstand page at <a href="http://autumnfox.akrasiac.org/hswc/noir">this link</a>.'
        csstype= 'roster_teamslots'
        count = get_team_members_count(teamname, cursor)
        captain = 'olympics-mods'
        return (csstype, count, teamname, captain, stringofallplayers)
    cursor.execute('SELECT * from teams where name=?', array)
    teamdatalist = cursor.fetchone()
    teamname = re.sub('<', '&lt;', teamdatalist[0])
    teamname = re.sub('>', '&gt;', teamname)
    if teamdatalist[5]:
        captain = teamdatalist[5]
    else: 
        captain = "None! You should sign up =D"
    count = teamdatalist[4]
    stringofallplayers = ''
    for x in cursor.execute('SELECT * from players where dwname=?', (teamdatalist[0])):
        stringofallplayers = stringofallplayers + ' ' + x[0]
    stringofallplayers = stringofallplayers.strip()
    csstype = 'roster_teamslots'
    if count < 4:
        csstype = 'roster_teamslots_small'
    if count > 7:
        csstype = 'roster_teamslots_full'
    return (csstype, count, teamname, captain, stringofallplayers)


def add_player_to_team(player, teamname, teamtype, fandom, cpnwilling, email, notes, cursor):
    """Adds a player to a team. If the team is full, errors out.
       If the player is already on the team, continue without changes.
       If the player is willing and there is no captain, Cpn them.
       If the team has at least 4 members, make it active."""
    #FINISHED FOR SASO
    if teamname == 'grandstand':
        add_player_to_grandstand(player, cursor)
        return
    
    if not team_exists(teamname, cursor):
        add_team(teamname, teamtype, fandom, cursor)
    
    if team_exists(teamname, cursor):
        array = (teamname,)
        cursor.execute('SELECT * from teams where team_name=?', array)
        teamdatalist = cursor.fetchone()
        alreadyonteam = 0 
        captain = teamdatalist[5]
        
        cursor.execute('SELECT * from players where dwname=?', (player,))
        player_info = cursor.fetchone()
        if player_info:
            if player_info[1] == teamdatalist[0]:
                alreadyonteam = 1
        
        # in theory being already on the team should have been caught earlier
        # but this will double-catch it just in case because not doing so is bad
        # also it is already written
        if not alreadyonteam:
            if teamdatalist[4] < 8:
                cursor.execute('UPDATE teams set num_participants = (num_participants + 1) where team_id=?', (teamdatalist[0],))
                cursor.execute('UPDATE players set team_id=? where dwname=?', (teamdatalist[0], player,))
                if player_info:
                    cursor.execute('UPDATE teams set num_participants = (num_participants - 1) where team_id=?', (player_info[1],))
                    cursor.execute('SELECT * from teams where team_id=?', (player_info[1],))
                    old_team = cursor.fetchone()
                    if old_team[5] == player:
                        cursor.execute("UPDATE teams set captain='' where team_id=?", (player_info[1],))
                        cursor.execute("UPDATE players set cpn=0 where dwname=?", (player,))
                        for x in cursor.execute("SELECT * from players where team_id=?", (player_info[1],)):
                            if x[6]:
                                make_captain(x[0], old_team[1], cursor)
                                break
                    if old_team[6] == player:
                        cursor.execute('UPDATE teams set vice_captain=? where team_id=?', ('', old_team[0]))
                        cursor.execute('UPDATE players set vice_captain=0 where dwname=?', (player))
                    if old_team[4] < 4:
                        cursor.execute("UPDATE teams set active=0 where team_id=?", (player_info[1],))
                if teamdatalist[4] == 0:
                    make_captain(player, teamname, cursor)
                elif not captain:
                    if cpnwilling:
                        make_captain(player, teamname, cursor)
                if teamdatalist[4] == 3:
                    cursor.execute('UPDATE teams set active = 1 where team_id=?', (teamdatalist[0],))
            else:
                return 'This team is already full! Sorry!'
        if not captain:
            if cpnwilling:
                make_captain(player, teamname, cursor)
        return
    else:
        return "Team doesn't exist after creating it, contact hurristat."
    return "This error should never happen! Contact hurristat." 

def scrub_team(team):
    """Return a valid team name based on the user input.
       If there is no valid team name, return nothing."""
    #FINISHED FOR SASO
    string = team.lower()
    string = string.strip()
    
    # if it has more than one ship symbol we are not touching this belunkus
    #i dont think this is necessary for saso but
    symbolcount = 0
    for x in ['<3<', '<3[^<]', '<>', 'c3<', 'o8<'] :
        if re.search(x, string):
            symbolcount = symbolcount + 1
    if symbolcount > 1:
        return string
    
    if string == '':
        return 0
    elif re.search('/', string):
        namelist = string.split('/')
        shipsymbol = '/'
    elif re.search('<3<', string):
        namelist = string.split('<3<')
        shipsymbol = '<3<'
    elif re.search('<3', string):
        namelist = string.split('<3')
        shipsymbol = '<3'
    elif re.search('<>', string):
        namelist = string.split('<>')
        shipsymbol = '<>'
    elif re.search('c3<', string):
        namelist = string.split('c3<')
        shipsymbol = 'c3<'
    elif re.search('o8<', string):
        namelist = string.split('o8<')
        shipsymbol = 'c3<'
    elif re.search('sports', string):
        return 'sports'
    elif re.search('grandstand', string):
        # grandstand won't show up, because there would be a ship symbol
        # unless you ship just... grandstands
        # no ship, just grandstands
        # in which case THE CODE CAN'T EVEN HANDLE YOU RIGHT NOW
        return 'grandstand'
    else:
        # then you have some kinda theme team or something whatever
        return string
    
    newlist = []
    newstring = ''
    
    for name in namelist:
        name = name.strip()
        newlist.append(name)
    
    newlist.sort()
    
    for x in range(0,(len(newlist) -1)):
        newstring = newstring + newlist[x] + shipsymbol
    
    newstring = newstring + newlist[-1]
    
    return newstring

def valid_fandom(fandom):
    #never do this, ever. why do people pay me to program
    fandom_new = fandom.split(',')
    for i in range(len(fandom_new)):
        fandom_new[i] = i.strip()
    fandom_list = ['Haikyuu!!', 'Daiya no Ace', 'Yowamushi Pedal', 'Free!' ,'Chihayafuru', 'Ookiku Furikabutte', 'Kuroko no Basuke', 'Ping Pong: The Animation', 'Eyeshield 21', 'Love Live!', 'Prince of Tennis', 'Hikaru no Go', 'Teppuu', 'Baby Steps' 'Slam Dunk', 'Angelic Layer']
    for i in range(len(fandom_new)):
        if not fandom_new[i] in fandom_list:
            return False
    return True

def get_newest_sports_team(fandom, cursor):
    cursor.execute("SELECT MAX(team_id) FROM teams WHERE fandom=? AND team_type='sports'", (fandom))
    newest_team = cursor.fetchone()
    cursor.execute("SELECT * FROM teams WHERE team_id=?", (newest_team[0]))
    newest_team_name = cursor.fetchone()
    return newest_team_name[1]

def get_newest_team(cursor):
    cursor.execute("SELECT MAX(team_id) FROM teams;")
    team_num = cursor.fetchone()
    return team_num[0]

if __name__ == "__main__":
    teamnames = ('rax<3<computers', 'modship<3players', 'h8rs<>h8rs')
    playernames = ('alice', 'bob', 'carol', 'dave', 'elsa', 'fiddlesticks')
    
    # add teams if they don't exist
    for team in teamnames:
        if team_exists(team):
            print "hooray"
        else:
            add_team(team)
    
    # print a list of all teams
    teamlist = get_list_of_teams()
    print teamlist 
   
    add_player_to_team('rax','rax<3<computers',0,'rax@akrasiac.org','')
    for player in playernames:
        add_player_to_team(player, 'rax<3<computers',0,'test@example.com','')
