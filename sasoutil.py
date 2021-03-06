#!/usr/bin/python

import sqlite3, sys, re, random
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

def send_inactives_to_grandstand():
    """Take players on inactive teams and send them to grandstand."""
    ##UPDATE FOR SASO, TEAM SETUP IS A LITTLE DIFFERENT
    ##MAYBE MAKE A SWITCH TEAM FUNCTION?
    allteams = get_list_of_teams()
    
    for team in allteams:
        if not is_team_active(team):
            players = get_team_members_list(team)
            for player in players:
                add_player_to_grandstand(player)
                remove_player_from_team(player, team)
    
    return

def make_cpn_list():
    """Make a list of all teams, their captains, and their email addresses."""
    #FINISHED FOR SASO
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where active=1')
    allteams = cursor.fetchall()
    bakedteams = []
    
    for team in allteams:
        if not team[5]:
            teamtuple = (team[1], 'none', 'none')
        else:
            cpn = team[5]
            email = get_player_email(cpn)
            teamtuple = (team[1], cpn, email)
        bakedteams.append(teamtuple)
    
    dbconn.commit()
    dbconn.close()
    
    return bakedteams

def get_player_email(player):
    """Get a player's email address."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    playerdata = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    
    if not playerdata:
        return "player does not exist"
    return playerdata[2]

def make_team_active(team):
    """Set the active bit on a team."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    string = """UPDATE teams set active=1 where name='%s'""" % team
    cursor.execute(string)
    
    dbconn.commit()
    dbconn.close()
    # whatever calls this has to dbconn.commit()
    return

def is_team_active(team):
    """Return the active bit on a team."""
    if team == 'grandstand':
        return 1
    
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (team,)
    cursor.execute('SELECT * from teams where team_name=?', array)
    thing = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    
    if thing:
        activebit = thing[7]
        return activebit
    # team does not exist
    return

def activate_qualifying_teams():
    """Set the active bit on all teams with 4 or more participants.
    And all teams that are abstrata."""

    teamlist = get_list_of_teams()
    for team in teamlist:
        count = get_team_members_count(team)
        if count >= 4:
            make_team_active(team)
    return

def make_pending_entry(dwname, email, team, captain, notes, team_type, fandom, minor):
    """Make a pending entry to be processed if the DW auth goes through."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (dwname, email, team_type, team, fandom, captain, notes, minor)
    cursor.execute('INSERT into pending (dwname, email, team_type, team, fandom, cpn_willing, notes, minor) values (?,?,?,?,?,?,?,?)', array)
    
    dbconn.commit()
    dbconn.close()
    return

def retrieve_pending_entry(dwname):
    """Get a pending entry out for a username."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (dwname,)
    cursor.execute('SELECT * from pending where dwname=?', array)
    pending_entry = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    return pending_entry

def remove_pending_entry(dwname):
    """Remove a pending entry for a username."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (dwname,)
    cursor.execute('DELETE from pending where dwname=?', array)
    
    dbconn.commit()
    dbconn.close()
    return

def make_pending_vote_entry(dwname):
    """make a pending vote entry to be processed if the DW auth goes through."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (dwname,)
    cursor.execute('INSERT into pending_vote (dwname) values (?)', array)
    
    dbconn.commit()
    dbconn.close()
    return

def team_exists(teamname):
    """See if a team exists in the database or not. If yes, return 1,
      if not return 0."""
    array = (teamname,) # for sanitizing
    if teamname == 'grandstand':
        return 1
    
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?', array)
    if cursor.fetchone():
        dbconn.commit()
        dbconn.close()
        
        return 1 
    else:
        dbconn.commit()
        dbconn.close()
        
        return 0 

def team_has_captain(teamname):
    """If a team has a friendleader, return 0, otherwise return 1"""
    array = (teamname,)
    if not team_exists(teamname):
        # there's not a friendleader if there's no team!
        return 0
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamlist = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    if teamlist[5]:
        return 1
    else:
        return 0

def player_exists(player):
    """See if a player exists in the database or not. If yes, return 1,
       if not return 0."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    if cursor.fetchone():
        dbconn.commit()
        dbconn.close()
        
        return 1
    else:
        dbconn.commit()
        dbconn.close()
        
        return 0

def get_current_team(player):
    """Get the team the player is currently on, if there is one."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    cursor.execute('SELECT * from players where dwname=?', array)
    currentteam = cursor.fetchone()
    if currentteam:
        cursor.execute('SELECT * from teams where team_id=?', (currentteam[1],))
        realteam = cursor.fetchone()
        
        dbconn.commit()
        dbconn.close()
        if realteam:
            return realteam[1]
        else:
            return 0
    else:
        dbconn.commit()
        dbconn.close()
        
        return 0
    
def add_team(teamname, teamtype, fandom):
    """Add a team to the database."""
    #UPDATED, MAY NEED FURTHER UPDATING
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    id_no = get_newest_team() + 1
    array = (id_no, teamname, teamtype, fandom, 0, '', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    cursor.execute('INSERT into teams (team_id, team_name, team_type, fandom, num_participants, captain, active, total_score, mr1, mr2, br0, br1, br2, br3, br4, br5, br6, penalty) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', array)
    
    dbconn.commit()
    dbconn.close()
    return

def remove_team(teamname):
    """Delete a team."""
    #FINISHED FOR SASO
    array = (teamname,)
    if teamname == 'grandstand':
        # don't delete grandstand
        return
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('DELETE from teams where team_name=?', array)
    
    dbconn.commit()
    dbconn.close()
    return

def remove_player(player):
    """Delete a player."""
    #FINISHED FOR SASO
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    cursor.execute('DELETE from players where dwname=?', array)
    
    dbconn.commit()
    dbconn.close()
    return

def get_list_of_teams():
    """Get a list of all teams."""
    #FINISHED FOR SASO
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    teamlist = []
    cursor.execute('SELECT * from teams where team_id = 0')
    teamlist.append(cursor.fetchone()[1])
    for team in cursor.execute('SELECT * from teams WHERE team_id != 0 ORDER BY num_participants ASC'):
        teamlist.append(team[1]) # man isn't it cool that order matters
    
    dbconn.commit()
    dbconn.close()
    # soni doesn't like it alphabetical
    # teamlist.sort()
    return teamlist

def get_teamcount():
    """Get a count of teams."""
    #FINISHED FOR SASO
    teamlist = get_list_of_teams()
    return len(teamlist)

def get_playercount():
    """Get a count of players."""
    #FINISHED FOR SASO
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    playerlist = []
    for player in cursor.execute('SELECT * from players'):
        playerlist.append(player[0])
    
    dbconn.commit()
    dbconn.close()
    return len(playerlist)

def get_captain(team):
    """Get the captain of a team, if one exists."""
    #FINISHED FOR SASO
    array = (team, )
    if not team_exists(team):
        return 0
    if team == 'grandstand':
        return 'saso mods'
    
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamrow = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    return teamrow[5]

def make_captain(player, teamname):
    """Make player captain of teamname."""
    #FINISHED FOR SASO
    
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player, teamname,)
    cursor.execute('UPDATE teams set captain=? where team_name=?', array)
    cursor.execute('UPDATE players set cpn=? where dwname=?', (1, player))
    #cursor.execute('UPDATE players set captain=? where dwname=?', ('yes', player))
    
    dbconn.commit()
    dbconn.close()
    return

def uncaptain(teamname):
    '''kill the captain of the ship, stage a mutiny'''
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (teamname,)
    cursor.execute('SELECT * from teams where team_name=?', array)
    team_info = cursor.fetchone()
    cursor.execute('UPDATE players set cpn=0 where dwname=?', (team_info[5],))
    cursor.execute("UPDATE teams set captain='' where team_name=?", array)
    
    dbconn.commit()
    dbconn.close()
    return

def remove_player_from_grandstand(player, deleting):
    """Remove a player from grandstand."""
    #FINISHED FOR SASO
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    #cursor.execute('DELETE from grandstand where dwname=?', array)
    #dbconn.commit()
    if deleting:
        cursor.execute('UPDATE players set team_id=-1 where dwname=?', array)
    cursor.execute('UPDATE teams set num_participants = (num_participants-1) where team_id=0')
    
    dbconn.commit()
    dbconn.close()
    return

def add_player_to_grandstand(player):
    """Add a player to grandstand."""
    #FINISHED FOR SASO
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    #cursor.execute('INSERT into grandstand (dwname) values (?)', array)
    cursor.execute('UPDATE players set team_id=? where dwname=?', (0, player))
    cursor.execute('UPDATE teams set num_participants = (num_participants + 1) where team_id=0')
    
    dbconn.commit()
    dbconn.close()
    return

def remove_player_from_team(player, teamname, deleting):
    """Remove a player from a team, presumably because they joined another."""
    #FINISHED FOR SASO
    array = (teamname,)
    if teamname == 'grandstand':
        remove_player_from_grandstand(player, deleting)
        return
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamdatalist = cursor.fetchone()
    if teamdatalist[5] == player:
        cursor.execute('UPDATE teams set captain=? where team_id=?', ('',teamdatalist[0]))
        cursor.execute('UPDATE players set cpn=0 where dwname=?', (player))
    if teamdatalist[6] == player:
        cursor.execute('UPDATE teams set vice_captain=? where team_id=?', ('', teamdatalist[0]))
        cursor.execute('UPDATE players set vice_captain=0 where dwname=?', (player))
    if deleting:
        cursor.execute('UPDATE players set team_id = -1 where dwname=?', (player,))
    cursor.execute('UPDATE teams set num_participants = (num_participants - 1) where team_id=?', (teamdatalist[0],))
    
    dbconn.commit()
    dbconn.close()
    return

def update_player(player, email, notes):
    """Update the player's information in the db after a new form submission."""
    #team does not change
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array=(email, notes, player)
    cursor.execute('UPDATE players set email=?, notes=? where dwname=?', array)
    
    dbconn.commit()
    dbconn.close()
    return

def add_player_to_players(player, email, cpnwilling, notes, minor):
    """Put the player in the player database at all.
       Team preference is not handled here."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array=(player, -1, cpnwilling, email, notes, minor)
    cursor.execute('INSERT into players (dwname, team_id, cpn_willing, email, notes, minor) values (?,?,?,?,?,?)', array)
    
    dbconn.commit()
    dbconn.close()
    return

def get_team_members_count(team):
    """How many players on the team?"""
    array=(team,)
    if not team_exists(team):
        return 0
    
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?',array)
    team_info = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    return team_info[4]

def get_team_members_list(team):
    """Who are the players on the team?"""
    array = (team,)
    if not team_exists(team):
        return 0
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamdatalist = cursor.fetchone()
    team_id = teamdatalist[0]
    teamplayers = []
    for x in cursor.execute('SELECT * from players where team_id=?', (team_id,)):
        if x[10] == 0:
            teamplayers.append(x[0] + '*')
        else:
            teamplayers.append(x[0])
    
    dbconn.commit()
    dbconn.close()
    return teamplayers

#def get_grandstand_members_count(cursor):
#    """How many players on team grandstand?"""
#    cursor.execute('SELECT * from grandstand')
#    grandstandlist = cursor.fetchall()
#    return len(grandstandlist)


#def get_grandstand_members_list(cursor):
#    """Which players are on team grandstand?"""
#    cursor.execute('SELECT * from grandstand')
#    grandstandlist = cursor.fetchall()
#    if not grandstandlist:
#        return ['nobody']
#    grandstandplayers = []
#    for x in grandstandlist:
#        grandstandplayers.append(x[0])
#    grandstandplayers.sort()
#    return grandstandplayers

#the schema of our database renders these functions unnecessary

def player_is_on_team(player, team):
    """Is the player on the team?"""
    array=(team,)
    if not team_exists(team):
        return 0
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?',array)
    teamdatalist = cursor.fetchone()
    team_team_id = teamdatalist[0]
    cursor.execute('SELECT * from players where dwname=?', (player,))
    playerlist = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    if playerlist:
        player_team_id = playerlist[1]
        if team_team_id == player_team_id:
            return 1
    return 0

def get_team_display_line(team):
    """Make the display line that goes into the teams table.
    Format is csstype, count, teamname, fl, stringofallplayers."""
    array=(team,)
    teamname = re.sub('<', '&lt;', team)
    teamname = re.sub('>', '&gt;', teamname)
    if teamname == 'grandstand':
        stringofallplayers = 'Please see the grandstand page at <a href="http://autumnfox.akrasiac.org/saso/grandstand">this link</a>.'
        csstype= 'roster_teamslots'
        count = get_team_members_count(teamname)
        captain = 'referees'
        return (csstype, count, teamname, captain, stringofallplayers)
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute('SELECT * from teams where team_name=?', array)
    teamdatalist = cursor.fetchone()
    teamname = re.sub('<', '&lt;', teamdatalist[1])
    teamname = re.sub('>', '&gt;', teamname)
    if teamdatalist[5]:
        captain = teamdatalist[5]
    else: 
        captain = "None! You should sign up =o"
    count = teamdatalist[4]
    stringofallplayers = ''
    for x in cursor.execute('SELECT * from players where team_id=?', (teamdatalist[0],)):
        stringofallplayers = stringofallplayers + ' ' + x[0]
	if x[10] == 0:
            stringofallplayers = stringofallplayers + '*'
    stringofallplayers = stringofallplayers.strip()
    csstype = 'roster_teamslots'
    if count < 4:
        csstype = 'roster_teamslots_small'
    if count > 7:
        csstype = 'roster_teamslots_full'
    
    dbconn.commit()
    dbconn.close()
    return (csstype, count, teamname, captain, stringofallplayers)


def add_player_to_team(player, teamname, teamtype, fandom, cpnwilling, email, notes, minor):
    """Adds a player to a team. If the team is full, errors out.
       If the player is already on the team, continue without changes.
       If the player is willing and there is no captain, Cpn them.
       If the team has at least 4 members, make it active."""
    if teamname == 'grandstand':
        add_player_to_grandstand(player)
        return
    
    if not team_exists(teamname):
        add_team(teamname, teamtype, fandom)
    
    if team_exists(teamname):
        dbconn = sqlite3.connect('saso.db')
        cursor = dbconn.cursor()
        
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
                if player_info[1] != -1:
                    #cursor.execute('UPDATE teams set num_participants = (num_participants - 1) where team_id=?', (player_info[1],))
                    cursor.execute('SELECT * from teams where team_id=?', (player_info[1],))
                    old_team = cursor.fetchone()
                    if old_team[5] == player:
                        cursor.execute("UPDATE teams set captain='' where team_id=?", (player_info[1],))
                        cursor.execute("UPDATE players set cpn=0 where dwname=?", (player,))
                        for x in cursor.execute("SELECT * from players where team_id=?", (player_info[1],)):
                            if x[6]:
                                make_captain(x[0], old_team[1])
                                break
                    if old_team[6] == player:
                        cursor.execute('UPDATE teams set vice_captain=? where team_id=?', ('', old_team[0]))
                        cursor.execute('UPDATE players set vice_captain=0 where dwname=?', (player))
                    if old_team[4] < 4:
                        cursor.execute("UPDATE teams set active=0 where team_id=?", (player_info[1],))
                if not teamdatalist[5]:
                    if cpnwilling:
                        make_captain(player, teamname)
                if teamdatalist[4] == 3:
                    cursor.execute('UPDATE teams set active = 1 where team_id=?', (teamdatalist[0],))
            else:
                dbconn.commit()
                dbconn.close()
                return 'This team is already full! Sorry!'
        if not teamdatalist[5]:
            if cpnwilling:
                make_captain(player, teamname)
        dbconn.commit()
        dbconn.close()
        return
    else:
        return "Team doesn't exist after creating it, contact hurristat."
    return "This error should never happen! Contact hurristat." 

def scrub_team(team):
    """Return a valid team name based on the user input.
       If there is no valid team name, return nothing."""
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
    if re.search(',', fandom):
        fandom_new = fandom.split(',')
        for i in range(len(fandom_new)):
            fandom_new[i] = fandom_new[i].strip()
    else:
        fandom_new = [fandom]
    fandom_list = ['Ace wo Nerae!', 'All Out!!', 'Angelic Layer', 'Ashita no Joe', 'Attacker You!', 'Baby Steps', 'Ballroom e Youkoso', 'Bamboo Blade', 'Battery', 'Cheer Danshi!!', 'Chihayafuru', 'Crimson Hero', 'Cross Game', 'Daiya no Ace', 'Dansui!', 'DAYS', 'DIVE!!', 'Eyeshield 21', 'Free!', 'Giant Killing', 'Gundam Build Fighters', 'H2', 'Haikyuu!!', 'Hajime no Ippo', 'Hanakaku', 'Hikari no Densetsu', 'Hikaru no Go', 'IGPX: Immortal Grand Prix', 'Inazuma Eleven', 'Initial D', 'Keijo!!!!!!!!!', 'Kuroko no Basuke', 'Last Inning', 'Long Riders!', 'Love Live!', 'Minami Kamakura High School Girls Cycling Club', 'Mononofu', 'Moshidora', 'Musashi no Ken', 'Ookiku Furikabutte', 'Ping Pong the Animation', 'Prince of Stride', 'The Prince of Tennis', 'Princess Nine', 'Robot x Laserbeam', 'Rookies', 'Saki', 'Shakunetsu no Takkyuu Musume', 'Shokugeki no Souma', 'Stella Women\'s Academy High School Division Class C3', 'Slam Dunk', 'Taishou Baseball Girls', 'Teppuu', 'Touch', 'Yawara!!', 'Yowamushi Pedal', 'Yuri!!! on Ice']
    for i in range(len(fandom_new)):
        if not fandom_new[i] in fandom_list:
            return False
    return True

def get_newest_sports_team(fandom):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT MAX(team_id) FROM teams WHERE fandom=? AND team_type='sports'", (fandom))
    newest_team = cursor.fetchone()
    cursor.execute("SELECT * FROM teams WHERE team_id=?", (newest_team[0]))
    newest_team_name = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    return newest_team_name[1]

def get_age_check(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT minor FROM players WHERE dwname=?", (dwname,))
    minor_level = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    return int(minor_level[0])

def update_minor_status(minor, dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (minor, dwname,)
    cursor.execute("UPDATE players SET minor=? WHERE dwname=?", array)
    
    dbconn.commit()
    dbconn.close()
    return

def check_pending_vote_entry(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT * FROM pending_vote")# WHERE dwname=?",(dwname,))
    cursor.fetchone()
    if cursor.fetchone():
        dbconn.commit()
        dbconn.close()
        return True
    else:
        dbconn.commit()
        dbconn.close()
        return False

def remove_pending_voting_entry(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("DELETE FROM pending_vote WHERE dwname=?", (dwname,))
    
    dbconn.commit()
    dbconn.close()
    return

def get_newest_team():
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT MAX(team_id) FROM teams;")
    team_num = cursor.fetchone()
    
    dbconn.commit()
    dbconn.close()
    return team_num[0]

def existing_voting_team_assignments(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT * FROM mr2_player_votes WHERE dwname = ?", (dwname,))
    if cursor.fetchone():
        dbconn.commit()
        dbconn.close()
        return 1
    else:
        dbconn.commit()
        dbconn.close()
        return 0

def assign_voting_assignments(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    current_team = get_current_team(dwname)
    cursor.execute("SELECT team_id FROM players WHERE dwname = ?", (dwname,))
    team_no = int(cursor.fetchone()[0])
    minor = get_age_check(dwname)
    current_teams = 10
    assigned_teams = []
    while len(assigned_teams) < 10:
        cursor.execute("SELECT * FROM mr2_team_votes WHERE players_assigned = (SELECT MIN(players_assigned) FROM mr2_team_votes)")
        team_list = cursor.fetchall()
        cont_empty = False
        if len(team_list) == 0:
            cont_empty = True
        while len(assigned_teams) < 10 and not cont_empty:
            todaysInt = random.randint(0, len(team_list) - 1)
            team_name = team_list[todaysInt][1]
            adult = team_list[todaysInt][3]
            if team_name not in assigned_teams and team_name != current_team and not (minor == 0 and adult == 1):
                assigned_teams.append(team_name)
                current_teams -= 1
                cursor.execute("UPDATE mr2_team_votes SET players_assigned = (players_assigned + 1) WHERE team_name = ?", (team_name,))
            team_list.pop(todaysInt)
            if len(team_list) == 0:
                cont_empty = True
    array = (dwname, team_no, 0, '', '', '', assigned_teams[0], assigned_teams[1], assigned_teams[2], assigned_teams[3], assigned_teams[4], assigned_teams[5], assigned_teams[6], assigned_teams[7], assigned_teams[8], assigned_teams[9],'',)
    cursor.execute("INSERT INTO mr2_player_votes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", array)
    
    dbconn.commit()
    dbconn.close()
    return

def get_vote_option_list(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    agg_list = []
    cursor.execute("SELECT * FROM mr2_player_votes WHERE dwname = ?", (dwname,))
    player_vote_list = cursor.fetchone()
    agg_list = [player_vote_list[6], player_vote_list[7], player_vote_list[8], player_vote_list[9], player_vote_list[10], player_vote_list[11], player_vote_list[12], player_vote_list[13], player_vote_list[14], player_vote_list[15]]
    
    dbconn.commit()
    dbconn.close()
    return agg_list

def enter_votes(dwname, vote1, vote2, vote3):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT vote_1, vote_2, vote_3 FROM mr2_player_votes WHERE dwname = ?", (dwname,))
    print vote1 + ' ' + vote2 + ' ' + vote3
    current_vote = cursor.fetchone()
    if current_vote and (current_vote[0] or current_vote[1] or current_vote[2]):
        cursor.execute("UPDATE mr2_team_votes SET votes = votes - 1 WHERE team_name = ?", (current_vote[0],))
        cursor.execute("UPDATE mr2_team_votes SET votes = votes - 1 WHERE team_name = ?", (current_vote[1],))
        cursor.execute("UPDATE mr2_team_votes SET votes = votes - 1 WHERE team_name = ?", (current_vote[2],))
    cursor.execute("UPDATE mr2_team_votes SET votes = votes + 1 WHERE team_name = ?", (vote1,))
    cursor.execute("UPDATE mr2_team_votes SET votes = votes + 1 WHERE team_name = ?", (vote2,))
    cursor.execute("UPDATE mr2_team_votes SET votes = votes + 1 WHERE team_name = ?", (vote3,))
    cursor.execute("UPDATE mr2_player_votes SET vote_1 = ? WHERE dwname = ?", (vote1, dwname,))
    cursor.execute("UPDATE mr2_player_votes SET vote_2 = ? WHERE dwname = ?", (vote2, dwname,))
    cursor.execute("UPDATE mr2_player_votes SET vote_3 = ? WHERE dwname = ?", (vote3, dwname,))
    
    dbconn.commit()
    dbconn.close()
    return 0

def create_entry_for_player(dwname):
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    cursor.execute("SELECT * FROM players WHERE dwname = ?", (dwname,))
    player = cursor.fetchone()
    team_id = player[1]
    array = (dwname, team_id, 0, '', '', '', '', '', '', '', '', '', '' ,'' ,'' ,'', '',)
    cursor.execute("INSERT INTO mr2_player_votes VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", array)
    
    dbconn.commit()
    dbconn.close()
    return

def player_vote_exists(player):
    """See if a player exists in the database or not. If yes, return 1,
       if not return 0."""
    dbconn = sqlite3.connect('saso.db')
    cursor = dbconn.cursor()
    
    array = (player,)
    cursor.execute('SELECT * from mr2_player_votes where dwname=?', array)
    if cursor.fetchone():
        dbconn.commit()
        dbconn.close()
        return 1
    else:
        dbconn.commit()
        dbconn.close()
        return 0

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
