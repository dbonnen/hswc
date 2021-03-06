#!/usr/bin/env python
"""
Cribbed off of python-openid's Simple example for an OpenID consumer.

The SASO signup page for 2017.
Almost all the code here was written for HSWC 2014 by the lovely raxraxraxraxrax@github
All SASO additions by dbonnen@github
"""

from Cookie import SimpleCookie
import cgi
import urlparse
import cgitb
import sys, re
import sasoutil as saso

#dbstuff
import sqlite3, sys


# MODES

#The default mode lets any authed user sign up for anything.
#mode = 'default' 

#The switch mode lets players switch off of sinking ships, join grandstand,
# or drop.
#mode = 'switch'

#The gs mode lets players drop, or join grandstand, but not switch to qualifying teams
#mode = 'gs'

#The drop mode only lets players drop.
mode = 'drop'

#main_round = 1
main_round = 2

voting_round = 1
#voting_round = 2

def quoteattr(s):
    qs = cgi.escape(s, 1)
    return '"%s"' % (qs,)

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

try:
    import openid
except ImportError:
    sys.stderr.write("""
Failed to import the OpenID library. In order to use this example, you
must either install the library (see INSTALL in the root of the
distribution) or else add the library to python's import path (the
PYTHONPATH environment variable).

For more information, see the README in the root of the library
distribution.""")
    sys.exit(1)

from openid.store import memstore
from openid.store import filestore
from openid.consumer import consumer
from openid.oidutil import appendArgs
from openid.cryptutil import randomString
from openid.fetchers import setDefaultFetcher, Urllib2Fetcher
from openid.extensions import pape, sreg



class OpenIDHTTPServer(HTTPServer):
    """http server that contains a reference to an OpenID consumer and
knows its base URL. The base URL is hardcoded here because that's how
it's set up in Apache2.
"""
    def __init__(self, store, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.sessions = {}
        self.store = store
        
        if self.server_port != 80:
            #self.base_url = ('http://%s:%s/' %
                              #(self.server_name, self.server_port))
             self.base_url = 'http://autumnfox.akrasiac.org/saso'
        else:
            self.base_url = 'http://%s/' % (self.server_name,)

class OpenIDRequestHandler(BaseHTTPRequestHandler):
    """Request handler that knows how to verify an OpenID identity."""
    SESSION_COOKIE_NAME = 'sasopage'
    
    session = None
    
    def getConsumer(self, stateless=False):
        if stateless:
            store = None
        else:
            store = self.server.store
        return consumer.Consumer(self.getSession(), store)
    
    def getSession(self):
        """Return the existing session or a new session"""
        if self.session is not None:
            return self.session
        
        # Get value of cookie header that was sent
        cookie_str = self.headers.get('Cookie')
        if cookie_str:
            cookie_obj = SimpleCookie(cookie_str)
            sid_morsel = cookie_obj.get(self.SESSION_COOKIE_NAME, None)
            if sid_morsel is not None:
                sid = sid_morsel.value
            else:
                sid = None
        else:
            sid = None
        
        # If a session id was not set, create a new one
        if sid is None:
            sid = randomString(16, '0123456789abcdef')
            session = None
        else:
            session = self.server.sessions.get(sid)
        
        # If no session exists for this session ID, create one
        if session is None:
            session = self.server.sessions[sid] = {}
        
        session['id'] = sid
        self.session = session
        return session
    
    def setSessionCookie(self):
        sid = self.getSession()['id']
        session_cookie = '%s=%s;' % (self.SESSION_COOKIE_NAME, sid)
        self.send_header('Set-Cookie', session_cookie)
    
    def do_GET(self):
        """Dispatching logic. There are multiple paths defined:

/ - Display an empty form asking for a signup
/verify - Handle form submission, initiating OpenID verification
/process - Handle a redirect from an OpenID server
/teams - display the teams as currently extant

Any other path gets a 404 response. This function also parses
the query parameters.

If an exception occurs in this function, a traceback is
written to the requesting browser.
"""
        try:
            self.parsed_uri = urlparse.urlparse(self.path)
            self.query = {}
            for k, v in cgi.parse_qsl(self.parsed_uri[4]):
                self.query[k] = v.decode('utf-8')
            
            path = self.parsed_uri[2]
            if path == '':
                path = '/' + self.parsed_uri[1] 
            if path == '/':
                self.render()
            elif path == '/verify':
                self.doVerify()
            elif path == '/process':
                self.doProcess()
            elif path == '/teams':
                self.doTeams()
            elif path == '/grandstand':
                self.doGrandstand()
            elif path == '/test':
                self.doTest()
            elif path == '/vote':
                self.doVote()
            elif path == '/voteverify':
                self.doVoteVerify()
            elif path == '/voting':
                self.renderVoting()
            elif path == '/voteaccept':
                self.acceptMessage()
            else:
                self.notFound()
        
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.setSessionCookie()
            self.end_headers()
            self.wfile.write(cgitb.html(sys.exc_info(), context=10))
    
    def doTest(self):
	"""fuck me"""
        self.send_response(200)
        self.wfile.write('''\
Content-type: text/html; charset=UTF-8
<head>
        <title>
        SASO 2017 GRANDSTAND ROSTER
        </title>
 
</head><body>
 
        <h1>
        SASO 2017 Grandstand Roster
        </h1>
 
</body>
</html>''')
	print "I got this far 3"
	return

    def doGrandstand(self):
        """Show the grandstand list page."""
        grandstandcount = str(saso.get_team_members_count('grandstand'))
        grandstandplayers = saso.get_team_members_list('grandstand')
        
        self.send_response(200)
        self.wfile.write('''\
Content-type: text/html; charset=UTF-8

<head>
        <title>
        SASO 2017 GRANDSTAND ROSTER
        </title>
 
        <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
        <meta http-equiv="refresh" content="300" />
        <meta name="dcterms.rights" content="Website Coding (C) 2014 HSWC Mod Team, 2015-17 SASO Mod Team" />
        <link rel="shortcut icon" href="http://i.imgur.com/wBU1Jzp.png">
 
        <style type="text/css" media="all">
html, body {   
        font-family: Verdana,Arial,"Liberation Sans",sans-serif;
        color: #000;
        font-size: 11pt;
        background-color: #e5e4e5;
}
 
a:link, a:visited {
        color: #3c3c89;
        font-weight:bold;
        text-decoration: none;
}
 
a:hover {
        color: #4e5273;
        font-weight:bold;
        text-decoration: underline;
}
 
h1 {
        font-size: 18pt;
        text-transform: uppercase;
        color: #3c3c89;
        text-align: center;
}
 
.navigation {
        margin-left: auto;
        margin-right: auto;    
        text-align: center;
        border-top: 1px #4e5273 solid;
        width:50%;
        padding: 22px 0px 10px 0px;
}
 
.tally {
        margin-left: auto;
        margin-right: auto;    
        text-align: center;
        background-color: #f9f9f9;
        padding: 3px;
        width: 540px;
        border-radius:10px;
}
 
table {
        width: 80%;
        background-color: #fff;
        padding: 20px;
        margin-left: auto;
        margin-right: auto;
        margin-top:1%;
        border-radius:10px;
        box-shadow:5px 5px #babad5;
}
 
.roster_teamname {
        background-color:#CCCCFF;
        font-size:15pt;
        text-transform:lowercase;
        width: 100%;
        text-align: right;
        padding: 7px;
}
 
.grandstand_members {
        padding: 3px 0px 15px 15px;
        text-transform:lowercase;
        width: 100%;
}
        </style>
</head><body>
 
        <h1>
        SASO 2016 Grandstand Roster
        </h1>''')
        
        self.wfile.write('''\
 
<p class="navigation"><a href="http://autumnfox.akrasiac.org/saso/">Sign Up Form</a> | <a href="http://autumnfox.akrasiac.org/saso/teams">Team Roster</a> | <a href="http://referees.dreamwidth.org/487.html">Mod Contact</a> | <a href="http://sportsanime.dreamwidth.org/">Dreamwidth</a> | <a href="http://sportsanime.dreamwidth.org/750.html">Rules</a> and <a href="http://sportsanime.dreamwidth.org/839.html">FAQ</a> | <a href="http://sportsanimeolympics.tumblr.com">Tumblr</a></p>
 
<p class="tally">
        There are currently <strong>%s participants</strong> in the grandstand.<br />
        This page will automatically update every <strong>5 minutes</strong>.
</p>
 
<table>
 
<tr>
        <td class="roster_teamname">
        Grandstand
        </td>
</tr>
<tr>
        <td class="grandstand_members">''' % grandstandcount)
        
        # MAGIC MARKER
        # DO GRANDSTAND LOGIC
        # THIS CODE SUCKS I AM TIRED
        
        grandstandlist = saso.get_team_members_list('grandstand')
        
        grandstanddict = {}
        for x in grandstandlist:
            firstchar = x[0]
            if firstchar in grandstanddict: 
                grandstanddict[firstchar] = grandstanddict[firstchar] + ', ' + x
            else:
                grandstanddict[firstchar] = x
        
        for x in ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','0','1','2','3','4','5','6','7','8','9']:
            if x in grandstanddict:
                self.wfile.write('''\
<p><span class="grandstand_%s" style="font-weight:bold;text-transform:none">%s:</span>%s</p>''' % (x,x, grandstanddict[x]))

        self.wfile.write('''\
</td>
</tr>
</table>
 
<p style="text-align:center;"><img src="http://i.imgur.com/98vfANt.png" alt="SPORTS!" /></p>
 
</body>
</html>''')


    def doTeams(self):
        """Show the page with all of the teams on it."""
        teamcount = str(saso.get_teamcount())
        playercount = str(saso.get_playercount())
        
        self.send_response(200)
        self.wfile.write('''\
Content-type: text/html; charset=UTF-8

<head>
	<title>
	SASO 2017 TEAM ROSTER
	</title>

	<meta http-equiv="content-type" content="text/html; charset=UTF-8" />
	<meta http-equiv="refresh" content="300" />
	<meta name="dcterms.rights" content="Website Coding (C) 2015-17 SASO Mod Team, 2014 HSWC Mod Team" />
        <link rel="shortcut icon" href="http://i.imgur.com/wBU1Jzp.png">

	<style type="text/css" media="all">
html, body {	
	font-family: Verdana,Arial,"Liberation Sans",sans-serif;
	color: #000;
	font-size: 11pt;
	background-color: #e5e4e5;
}

a:link, a:visited {
	color: #3c3c89;
	font-weight:bold;
	text-decoration: none;
}

a:hover {
	color: #4e5273;
	font-weight:bold;
	text-decoration: underline;
}

h1 {
	font-size: 18pt;
	text-transform: uppercase;
	color: #3c3c89;
	text-align: center;
}

.navigation {
	margin-left: auto;
	margin-right: auto;	
	text-align: center;
	border-top: 1px #4e5273 solid;
	width:50%;
	padding: 22px 0px 10px 0px;
}

.tally {
	margin-left: auto;
	margin-right: auto;	
	text-align: center;
	background-color: #f9f9f9;
	padding: 3px;
	width: 540px;
	border-radius:10px;
}

table {
	width: 80%;
	background-color: #fff;
	padding: 20px;
	margin-left: auto;
	margin-right: auto;
	margin-top:1%;
	border-radius:10px;
	box-shadow:5px 5px #babad5;
}

.roster_teamname {
	background-color:#CCCCFF;
	font-size:15pt;
	text-transform:lowercase;
	width: 94%;
	text-align: right;
	padding: 7px;
}

.roster_teamslots {
	background-color: #FA8072;
	width: 6%;
	text-align: center;
}

.roster_teamslots_full {
	background-color: #EED5D2;
	width: 6%;
	text-align: center;
}

.roster_teamslots_small {
	background-color: #CC1100;
	color: #fff;
	width: 6%;
	text-align: center;
}

.roster_cpn {
	padding: 7px 0px 5px 15px;
	border-bottom: 1px dotted #babad5;
	text-transform:lowercase;
}

.roster_members {
	padding: 3px 0px 15px 15px;
	text-transform:lowercase;
}
	</style>
</head>''')

	self.wfile.write('''\
<body>

	<h1>
	SASO 2017 Team Roster
	</h1>

<p class="navigation"><a href="http://autumnfox.akrasiac.org/saso/">Sign Up Form</a> | <a href="http://autumnfox.akrasiac.org/saso/teams">Team Roster</a> | <a href="http://referees.dreamwidth.org/487.html">Mod Contact</a> | <a href="http://sportsanime.dreamwidth.org/">Dreamwidth</a> | <a href="http://sportsanime.dreamwidth.org/750.html">Rules</a> and <a href="http://sportsanime.dreamwidth.org/839.html">FAQ</a> | <a href="http://sportsanimeolympics.tumblr.com">Tumblr</a></p>

<p class="tally">
	There are currently <strong>%s teams</strong> and <strong>%s participants</strong>.<br />
	This page will automatically update every 5 minutes.
</p>

<p class="tally"> An asterisk (*) indicates that a participant is a minor.</p>

<table>''' % (teamcount,playercount))
        
        allteams = saso.get_list_of_teams()
        for team in allteams:
            displayline = saso.get_team_display_line(team)
            if team != 'grandstand':
                self.wfile.write('''\
<tr>
	<td class="%s">
	%s/8
	</td>

	<td class="roster_teamname">
	%s
	</td>
</tr>
<tr>
	<td colspan="2" class="roster_cpn">
	<span style="font-weight:bold;text-transform:none">Captain:</span> %s 
	</td>
</tr>
<tr>
	<td colspan="2" class="roster_members">
	<span style="font-weight:bold;text-transform:none">Members:</span> %s
	</td>
</tr>''' % displayline)
            else:
                self.wfile.write('''\
<tr>
        <td class="%s">
        %s
        </td>

        <td class="roster_teamname">
        %s
        </td>
</tr>
<tr>
        <td colspan="2" class="roster_cpn">
        <span style="font-weight:bold;text-transform:none">Captain:</span> %s 
        </td>
</tr>
<tr>
        <td colspan="2" class="roster_members">
        <span style="font-weight:bold;text-transform:none">Members:</span> %s
        </td>
</tr>''' % displayline)

        self.wfile.write('''\
</table>

<p style="text-align:center"><img src="http://i.imgur.com/98vfANt.png" alt="SPORTS!" /></p>

</body>
</html>''')
    
    
    def doVerify(self):
        """Process the form submission, initating OpenID verification.
        """
        
        # First, collect all the data.
        openid_url = self.query.get('username')
        minor = self.query.get('minor')
        if minor == 'yes':
            minor = 1
        else:
            minor = 0
        email = self.query.get('email')
        team_type = self.query.get('team_type')
        team = self.query.get('team')
        fandom = self.query.get('fandom')
        contentnotes = self.query.get('contentnotes')
        
        if not openid_url:
            self.render('Please enter your dreamwidth username.', css_class='error',
                        form_contents=(openid_url,minor, email, team_type, team, fandom, contentnotes))
            return
        if openid_url:
            openid_url = re.sub('_','-',openid_url)
            openid_url = openid_url.lower()
        if team:
            # everything depends on unicode type strings BUT
            # if someone tries to paste in unicode ship symbols everything goes to hell
            team = team.lower()
            lower_fandom = ''
            if fandom:
                lower_fandom = fandom.lower()
            asciiteam = team.encode('ascii', 'ignore')
            convertedteam = unicode(asciiteam)
            if team_type == 'grandstand' and team != 'grandstand' and team != 'remove':
                self.render('Please enter "Grandstand" for the team name if you want to join the Grandstand.', css_class='error',
                            form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
            if not team == convertedteam:
                self.render('Please do not use unicode characters in team names.', css_class='error',
                            form_contents=(openid_url,email,minor, team_type,team,fandom,contentnotes))
                return
            if team_type == 'ship' and '/' not in team and team != 'remove':
                self.render('Ship teams must be composed of two or more character names.', css_class='error',
                            form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
            if team_type == 'sports' and '/' in team and team != 'remove':
                self.render('Sports teams cannot be made of one ship.', css_class='error',
                            form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
            if team_type == 'sports' and lower_fandom != team and team != 'remove':
                self.render('Sports teams must be named the same as the anime or manga it is from.', css_class='error',
                            form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
            team = saso.scrub_team(team)
        if fandom:
            if not saso.valid_fandom(fandom) and team_type != 'grandstand':
                self.render('Please only enter pairings and teams from nominated fandoms. If your fandom is nominated, please spell it the same way it is spelled on the list of nominated fandoms.', css_class='error',
                            form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
        elif team != 'grandstand':
            self.render('Please enter the anime/manga your team belongs to.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        if self.query.get('CPN') == 'yes':
            cpnwilling = 1
        else:
            # if they didn't check anything we assume they do not want to
            # be a captain. that seems best here.
            cpnwilling = 0
        #contentnotes = self.query.get('content-tags')
        # You have to even enter the rules check.
        if not self.query.get('rules-check'):
            self.render('Please enter the rules check text.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        # You have to get the rules check right.
        if (self.query.get('rules-check')).strip() != 'I certify that I have read and will abide by the Rules and Regulations of the 2017 SASO.':
            self.render('Please enter the correct rules check text.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        # There has to be a team name.
        if not team:
            self.render('Please enter a team name.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        if re.search('team', team) or re.search('&', team) or re.search(';', team):
            self.render('Team formatted incorrectly, see <a href="http://sportsanime.dreamwidth.org/2696.html#formatting">How To Format Ship Names</a>.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        team = saso.scrub_team(team)
        if not team:
            self.render('Please enter a valid team name.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        # There also has to be an email address!
        if not email:
            self.render('Please enter an email address.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        if not re.match(r'[^@]+@[^@]+\.[^@]+',email):
            self.render('Please enter a valid email address.', css_class='error',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
        # There has to be a username.
        if not openid_url:
            self.render('Please enter a Dreamwidth username.',
                        css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return 
        # If mode is switch, new players can only join grandstand,
        #                    players on qualifying teams can only drop,
        #                    players on non-qualifying teams can switch to qualifying ones or drop
        if mode == "switch":
            if not saso.player_exists(openid_url):
                if not team == 'grandstand':
                    self.render('Sorry, new players can only join Team Grandstand at this point.',
                                css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
            currentteam = saso.get_current_team(openid_url)
            if saso.is_team_active(currentteam):
                if not team == 'remove':
                    self.render('Sorry, players on qualifying teams can only drop.',
                                css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
            if not saso.is_team_active(team):
                if not team == 'remove':
                    self.render('Sorry, you can only join a qualifying team.',
                                css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
        #New players can join grandstand if the mode is gs, and existing users can drop,
        #but no one else can switch
        if mode == 'gs':
            if not saso.player_exists(openid_url):
                if not team_type == 'grandstand':
                    self.render('Sorry, new players can only join Team Grandstand at this point.',
                                css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
            elif not team == 'remove':
                    self.render('Sorry, players on qualifying teams can only drop.',
                                css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
        # If mode is drop, all you can do is drop. That's it.
        if mode == "drop":
            if team != 'remove':
                self.render('Sorry, at this point in the event all you can do is drop.',
                            css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
        
        # The team can't be full. 
        if saso.get_team_members_count(team) >= 8 and team_type != 'grandstand' and team_type != 'sports':
            if not saso.player_is_on_team(openid_url, team):
                self.render('That team is full, sorry. Try signing up for another one!',
                            css_class='error', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
        
        if saso.get_team_members_count(team) >= 8 and team_type == 'sports':
            #this code only works if you assume that there will be less than 80 people signing up for one fandom
            #this is in no way scalable and you shouldn't do this
            newest_team = saso.get_newest_sports_team(fandom)
            if saso.get_team_members_count(newest_team) >= 8:
                if newest_team[-1].isdigit():
                    team_num = int(newest_team[-1])
                    team = team + " " + str(team_num + 1)
                else:
                    team = team + " " + str(2)
            else:
                team = newest_team
        
        # We want this to go through, so we make an entry in the pending table.
        saso.make_pending_entry(openid_url, email, team, cpnwilling, contentnotes, team_type, fandom, minor)
        
        # Now add the DW part of the string --- we don't want other OpenID
        # providers because they are cubeless and shall surely be put to
        # death.
        openid_url = openid_url + '.dreamwidth.org'
        
        # we're not using these parts of the example but I did not strip them
        # out on the theory that we might end up needing them for some reason
        #immediate = 'immediate' in self.query
        #use_sreg = 'use_sreg' in self.query
        #use_pape = 'use_pape' in self.query
        #use_stateless = 'use_stateless' in self.query
        immediate = 0
        use_sreg = 0
        use_pape = 0
        use_stateless = 0
        
        oidconsumer = self.getConsumer(stateless = use_stateless)
        try:
            request = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure, exc:
            fetch_error_string = 'Error in discovery: %s' % (
                cgi.escape(str(exc[0])))
            self.render(fetch_error_string,
                        css_class='error',
                        form_contents=openid_url)
        else:
            if request is None:
                msg = 'No OpenID services found for <code>%s</code>' % (
                    cgi.escape(openid_url),)
                self.render(msg, css_class='error', form_contents=openid_url)
            else:
                # Then, ask the library to begin the authorization.
                # Here we find out the identity server that will verify the
                # user's identity, and get a token that allows us to
                # communicate securely with the identity server.
                if use_sreg:
                    self.requestRegistrationData(request)
                
                if use_pape:
                    self.requestPAPEDetails(request)
                
                trust_root = self.server.base_url
                #print 'trust_root is ' + trust_root
                return_to = self.buildURL('process')
                #print 'return_to is ' + return_to
                if request.shouldSendRedirect():
                    redirect_url = request.redirectURL(
                        trust_root, return_to, immediate=immediate)
                    self.send_response(302)
                    self.send_header('Location', redirect_url)
                    self.writeUserHeader()
                    self.end_headers()
                else:
                    form_html = request.htmlMarkup(
                        trust_root, return_to,
                        form_tag_attrs={'id':'openid_message'},
                        immediate=immediate)
                    
                    self.wfile.write(form_html)
    
    def requestRegistrationData(self, request):
        sreg_request = sreg.SRegRequest(
            required=['nickname'], optional=['fullname', 'email'])
        request.addExtension(sreg_request)
    
    def requestPAPEDetails(self, request):
        pape_request = pape.Request([pape.AUTH_PHISHING_RESISTANT])
        request.addExtension(pape_request)
    
    def doProcess(self):
        """Handle the redirect from the OpenID server.
"""
        oidconsumer = self.getConsumer()
        
        # Ask the library to check the response that the server sent
        # us. Status is a code indicating the response type. info is
        # either None or a string containing more information about
        # the return type.
        # url = 'http://'+self.headers.get('Host')+self.path
        # rax: hardcoding this for maximum bullshit
        # this makes me not just a bad programmer but a bad person
        url = 'http://autumnfox.akrasiac.org/saso/'+ self.path.strip('/')
        info = oidconsumer.complete(self.query, url)
        
        sreg_resp = None
        pape_resp = None
        css_class = 'error'
        display_identifier = info.getDisplayIdentifier()
        # There has to be a username.
        if not display_identifier:
            self.render('Please enter a Dreamwidth username.',
                        css_class='error', form_contents=('','','',''))
            return
        dwname = (display_identifier.split('.')[0]).split('//')[1]
        openid_url = dwname
        
        pending_entry = saso.retrieve_pending_entry(dwname)
        if not pending_entry:
            self.render('The software choked and lost your preferences, sorry. Kick hurristat.',
                css_class='error', form_contents=(dwname,'','',''))
            return
        
        email = pending_entry[1]
        team_type = pending_entry[2]
        team = pending_entry[3]
        fandom = pending_entry[4]
        cpn_willing = pending_entry[5]
        contentnotes = pending_entry[6]
        minor = pending_entry[8]
        saso.remove_pending_entry(dwname)
        
        if info.status == consumer.FAILURE and display_identifier:
            # In the case of failure, if info is non-None, it is the
            # URL that we were verifying. We include it in the error
            # message to help the user figure out what happened.
            fmt = "Verification of %s failed: %s"
            message = fmt % (cgi.escape(display_identifier),
                             info.message)
        elif info.status == consumer.SUCCESS:
            # Success means that the transaction completed without
            # error. If info is None, it means that the user cancelled
            # the verification.
            css_class = 'alert'
            
            # This is a successful verification attempt. Since this
            # is now a real application, we do stuff with the form data.
            # Or at least will.
            fmt = "You have successfully signed up with %s as your identity."
            message = fmt % (cgi.escape(display_identifier),)
            # ACTUALLY DO SHIT
            #sreg_resp = sreg.SRegResponse.fromSuccessResponse(info)
            #pape_resp = pape.Response.fromSuccessResponse(info)
            
            # MAGIC MARKER 
            
            # If they're not in the database yet at all, add them without a team.
            # This way they're logged even if their team falls through for some reason
            # and we can track them down. Plus we can now depend on them existing
            # for the rest of this code block.
            if not saso.player_exists(openid_url):
                saso.add_player_to_players(openid_url, email, cpn_willing, contentnotes, minor)
            
            teamclean = re.sub('<', '&lt;', team)
            teamclean = re.sub('>', '&gt;', teamclean)
            if team == 'remove':
                currentteam = saso.get_current_team(openid_url)
                if not currentteam:
                    self.render('Cannot remove you from no team.', css_class='error',
                                form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
                currentteamclean = re.sub('<', '&lt;', currentteam)
                currentteamclean = re.sub('>', '&gt;', currentteamclean)
                saso.remove_player_from_team(openid_url, currentteam, 1)
                saso.remove_player(openid_url)
                self.render('Removed you from team %s and the event.' % currentteamclean, css_class='alert',
                            form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
            
            #If the player is already on the team, just update 
            if saso.player_is_on_team(openid_url, team):
                # this got stringified by putting it into the db and taking it out again
                # THAT'S WHY NOTHING WAS WORKING
                
                #if they accidentally say they are a minor when they are not or vice versa
                old_minor_status = saso.get_age_check(openid_url)
                if old_minor_status == 0 or old_minor_status == 1:
                    if old_minor_status != minor:
                        saso.update_minor_status(minor, openid_url)
                        self.render('Changed age status.', css_class='alert',
                                    form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                        return
                
                if not cpn_willing:
                    # they don't want to be captain so nothing changes unless they already are
                    if saso.get_captain(team) == openid_url:
                        saso.uncaptain(team)
                        self.render('You are no longer the captain of %s.' % teamclean, css_class='alert',
                                    form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                        return
                    saso.update_player(openid_url, email, contentnotes)
                    self.render('No change to team, personal information updated.', css_class='alert',
                                form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
                else:
                    # they do want to be captain so if no one else is, they get the slot
                    if not saso.team_has_captain(team):
                        saso.make_captain(openid_url, team)
                        saso.update_player(openid_url, email, contentnotes)
                        self.render('Became captain of %s.' % teamclean, css_class='alert',
                                    form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                        return
                    else:
                        saso.update_player(openid_url, email, contentnotes)
                        self.render('No change to team, personal information updated.', css_class='alert',
                                    form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                        return
            # Try to add them to whatever team they want to be on.
            oldteam = saso.get_current_team(openid_url)
            errorstatus = saso.add_player_to_team(openid_url, team, team_type, fandom, cpn_willing, email, contentnotes, minor)
            teamclean = re.sub('<', '&lt;', team)
            teamclean = re.sub('>', '&gt;', teamclean)
            if errorstatus:
                # some belunkus error got passed back, don't remove from old team
                self.render(errorstatus, css_class='alert', form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                return
            if oldteam:
                if oldteam != team:
                    saso.remove_player_from_team(openid_url, oldteam, 0)
                    oldteamclean = re.sub('<', '&lt;', oldteam)
                    oldteamclean = re.sub('>', '&gt;', oldteamclean)
                    self.render('%s added to %s and removed from %s!' % (openid_url, teamclean, oldteamclean), css_class='alert', 
                                form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
                    return
            
            self.render('Added %s to %s!' % (openid_url, teamclean), css_class='alert',
                        form_contents=(openid_url, email, minor, team_type, team, fandom, contentnotes))
            return
            
        elif info.status == consumer.CANCEL:
            # cancelled
            message = 'Verification cancelled'
        elif info.status == consumer.SETUP_NEEDED:
            if info.setup_url:
                message = '<a href=%s>Setup needed</a>' % (
                    quoteattr(info.setup_url),)
            else:
                # This means auth didn't succeed, but you're welcome to try
                # non-immediate mode.
                message = 'Setup needed'
        else:
            # Either we don't understand the code or there is no
            # openid_url included with the error. Give a generic
            # failure message. The library should supply debug
            # information in a log.
            message = 'Verification failed.'
        
        self.render(message, css_class, display_identifier,
                    sreg_data=sreg_resp, pape_data=pape_resp)
    
    def buildURL(self, action, **query):
        """Build a URL relative to the server base_url, with the given
query parameters added."""
        # ugly hacks that work work
        base = self.server.base_url + '/' + action
        return appendArgs(base, query)
    
    def notFound(self):
        """Render a page with a 404 return code and a message."""
        fmt = 'The path <q>%s</q> was not understood by this server.'
        msg = fmt % (self.path,)
        openid_url = self.query.get('openid_identifier')
        self.render(msg, 'error', openid_url, status=404)
    
    def render(self, message=None, css_class='alert', form_contents=None,
               status=200, title="Sports Anime Shipping Olympics",
               sreg_data=None, pape_data=None):
        """Render the signup page."""
        self.send_response(status)
        self.pageHeader(title)
        if message:
            #print message
            self.wfile.write("<div class='%s'>" % (css_class,))
            self.wfile.write(message)
            self.wfile.write("</div>")
        self.pageFooter(form_contents)
    
    def pageHeader(self, title):
        """Render the page header"""
        self.setSessionCookie()
        #print (title, title, quoteattr(self.buildURL('verify')))
        self.wfile.write('''\
Content-type: text/html; charset=UTF-8

<head>
	<title>
	SASO 2017 SIGNUPS
	</title>

	<meta http-equiv="content-type" content="text/html; charset=UTF-8" />
	<meta http-equiv="refresh" content="50000" />
	<meta name="dcterms.rights" content="Website Coding (C) 2015-17 SASO Mod Team, 2014 HSWC Mod Team" />
	<link rel="shortcut icon" href="http://i.imgur.com/wBU1Jzp.png">

	<style type="text/css" media="all">
html, body {	
	font-family: Verdana,Arial,"Liberation Sans",sans-serif;
	color: #000;
	font-size: 11pt;
	background-color: #e5e4e5;
}

a:link,a:visited {
	color: #3c3c89;
	font-weight:bold;
	text-decoration: none;
}

a:hover {
	color: #4e5273;
	font-weight:bold;
	text-decoration: underline;
}

h1 {
	font-size: 18pt;
	text-transform: uppercase;
	color: #3c3c89;
	text-align: center;
}

.navigation {
	margin-left: auto;
	margin-right: auto;	
	text-align: center;
	border-top: 1px #4e5273 solid;
	width:50%;
	padding: 22px 0px 10px 0px;
}

.alert {
	border: 2px solid #e7dc2b;
	margin: 0px 10px 20px 0px;
	padding: 7px;
	background-color: #fff888;
	font-weight: bold;
	text-align: center;
	margin-left: auto;
	margin-right: auto;
	width: 70%;
}

.error {
	border: 2px solid #ff0000;
	margin: 0px 10px 20px 0px;
	padding: 7px;
	background-color: #ffaaaa;
	font-weight: bold;
	text-align: center;
	margin-left: auto;
	margin-right: auto;
	width: 70%;
}

form {
	width: 70%;
	background-color: #fff;
	padding: 20px;
	margin-left: auto;
	margin-right: auto;
	margin-top:1%;
	border-radius:10px;
	box-shadow:5px 5px #babad5;
}

.edit { 
	border: 2px #4e5273 solid;
	margin: 7px;
	padding: 7px;
	background-color: #f1f1f1;
	}

input, textarea {
	border: 1px solid black;
	background-color: #fff;
	margin: 3px 0px 0px 0px;
}

.field {
	font-weight:bold
	}

.descrip {
	font-size:10pt;
	color:#202020;
}
	</style>
</head>

<body>

	<h1>
	SASO 2017 Sign Up Form
	</h1>

<p class="navigation"><a href="http://autumnfox.akrasiac.org/saso/teams">Team Roster</a> | <a href="http://referees.dreamwidth.org/487.html">Mod Contact</a> | <a href="http://sportsanime.dreamwidth.org">Dreamwidth</a> | <a href="http://sportsanime.dreamwidth.org/750.html">Rules</a> | <a href="http://sportsanimeolympics.tumblr.com">Tumblr</a></p>''')
    
    def pageFooter(self, form_contents):
        """Render the page footer"""
        if not form_contents:
            form_contents = ''
        self.wfile.write('''\
<form method="GET" accept-charset="UTF-8" action=%s>
<p class="edit">
	<strong>To edit your sign up for any reason</strong> (typos, wrong 
e-mail, switching teams, new content tags, etc.), just sign up 
again. You won't lose your current team spot (unless you're 
switching teams).
</p>

<p>
	<span class="field">Dreamwidth Username:</span><br />
	<span class="descrip">You need a <a href="https://www.dreamwidth.org/create">DW account</a>. Make sure it's <a href="http://www.dreamwidth.org/register">verified</a>!</span><br />
	<input name="username" type="text" />
</p>

<p>
	<span class="field">E-mail Address:</span><br />
	<input name="email" type="text" />
</p>

<p>
        <span class="field">Are you 18 or older?</span>
        <input name="minor" value="yes" type="radio"/>Yes <input name="minor" type="radio" value="no" checked />No
</p>

<p>
    <span class="field">What type of team are you joining?</span><br />
    <input name="team_type" value="ship" type="radio" />Ship Team &nbsp; <input name="team_type" value="sports" type="radio" />Sports Team &nbsp; <input name="team_type" type="radio" value="grandstand" checked/>Grandstand
</p>

<p>
	<span class="field">Joining SASO Team:</span><br />
	<span class="descrip">Format your team name <a href="http://sportsanime.dreamwidth.org/11870.html#cutid1">like this</a>! Enter "Grandstand" if you're joining the Team Grandstand.</span><br />
	<input name="team" type="text" />
</p>

<p>
    <span class="field">What anime/manga is this ship/team from?</span><br />
    <span class="descrip">Please leave this blank if you're joining Team Grandstand. If you have a cross-fandom ship, please list all shows, and separate them with commas. If the canon has multiple names or you are unsure of how to spell it, there is a list <a href="http://sportsanime.dreamwidth.org/19182.html#cutid1">here</a>.</span><br />
    <input name="fandom" type="text" />
</p>

<p>
	<span class="field">Would you like to volunteer to be the team's <a href="http://sportsanime.dreamwidth.org/750.html#teams">Captain</a>?:</span><br />
	<input name="CPN" value="yes" type="radio" />Yes &nbsp; <input name="CPN" value="no" type="radio" checked/>No
</p>

<p>
	<span class="field">Any noteworthy content tags that you would like to add and are not already listed on the <a href="http://sportsanime.dreamwidth.org/1609.html">content tags list?</a>:</span> <br />
	<span class="descrip">The major content tags are used to warn for 
content that may be potentially upsetting and is not a place for 
sarcastic comments or jokes. Misusing the tag request form may result in
 your removal from SASO.</span><br />
	<textarea name="contentnotes" rows="5" cols="70">&nbsp;</textarea>
</p>

<p>
	<span class="field"><a href="http://sportsanime.dreamwidth.org/2057.html">Participant Agreement</a>'s rules check phrase:</span><br />
	<input name="rules-check" type="text" />
</p>

<input type="submit" value="Sign up!">

</form>

<p style="text-align:center"><img src="http://i.imgur.com/98vfANt.png" alt="SPORTS!" /></p>

</body></html>
''' % (quoteattr(self.buildURL('verify')),))
    
    def doVote(self, message=None, css_class='alert', form_contents=None,
               status=200, title="Sports Anime Shipping Olympics",
               sreg_data=None, pape_data=None):
        """Render the signup page."""
        self.send_response(status)
        self.votePage(title, form_contents)
        if message:
            #print message
            self.wfile.write("<div class='%s'>" % (css_class,))
            self.wfile.write(message)
            self.wfile.write("</div>")
    
    
    def votePage(self, title, form_contents):
        """Render the page header"""
        self.setSessionCookie()
        self.send_response(200)
        self.wfile.write('''\
Content-type: text/html; charset=UTF-8

<head>
    <title>
    SASO 2017 VOTING
    </title>

    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <meta http-equiv="refresh" content="50000" />
    <meta name="dcterms.rights" content="Website Coding (C) 2015-17 SASO Mod Team, 2014 HSWC Mod Team" />
    <link rel="shortcut icon" href="http://i.imgur.com/wBU1Jzp.png">

    <style type="text/css" media="all">
html, body {    
    font-family: Verdana,Arial,"Liberation Sans",sans-serif;
    color: #000;
    font-size: 11pt;
    background-color: #e5e4e5;
}

a:link,a:visited {
    color: #3c3c89;
    font-weight:bold;
    text-decoration: none;
}

a:hover {
    color: #4e5273;
    font-weight:bold;
    text-decoration: underline;
}

h1 {
    font-size: 18pt;
    text-transform: uppercase;
    color: #3c3c89;
    text-align: center;
}

.navigation {
    margin-left: auto;
    margin-right: auto; 
    text-align: center;
    border-top: 1px #4e5273 solid;
    width:50%;
    padding: 22px 0px 10px 0px;
}

.alert {
    border: 2px solid #e7dc2b;
    margin: 0px 10px 20px 0px;
    padding: 7px;
    background-color: #fff888;
    font-weight: bold;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
    width: 70%;
}

.error {
    border: 2px solid #ff0000;
    margin: 0px 10px 20px 0px;
    padding: 7px;
    background-color: #ffaaaa;
    font-weight: bold;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
    width: 70%;
}

form {
    width: 70%;
    background-color: #fff;
    padding: 20px;
    margin-left: auto;
    margin-right: auto;
    margin-top:1%;
    border-radius:10px;
    box-shadow:5px 5px #babad5;
}

.edit { 
    border: 2px #4e5273 solid;
    margin: 7px;
    padding: 7px;
    background-color: #f1f1f1;
    }

input, textarea {
    border: 1px solid black;
    background-color: #fff;
    margin: 3px 0px 0px 0px;
}

.field {
    font-weight:bold
    }

.descrip {
    font-size:10pt;
    color:#202020;
}
    </style>
</head>

<body>

    <h1>
    SASO 2017 VOTING FORM
    </h1>

<p class="navigation"><a href="http://autumnfox.akrasiac.org/saso/teams">Team Roster</a> | <a href="http://referees.dreamwidth.org/487.html">Mod Contact</a> | <a href="http://sportsanime.dreamwidth.org">Dreamwidth</a> | <a href="http://sportsanime.dreamwidth.org/750.html">Rules</a> | <a href="http://sportsanimeolympics.tumblr.com">Tumblr</a></p>

<form method="GET" accept-charset="UTF-8" action=/saso/voteverify>
<p>
    <span class="field">Dreamwidth Username:</span><br />
    <span class="descrip">Please enter your dreamwidth username</span><br />
    <input name="username" type="text" />
</p>

<input type="submit" value="Submit">
</form>

<p style="text-align:center"><img src="http://i.imgur.com/98vfANt.png" alt="SPORTS!" /></p>

</body></html>
''')
    
    def doVoteVerify(self):
        openid_url = self.query.get('username')
        openid_url = re.sub('_','-',openid_url)
        if openid_url:
            openid_url = openid_url.lower()
        
        if not saso.player_exists(openid_url):
            self.doVote('Only participants can vote for main round entries.', css_class='error', form_contents=(openid_url))
        
        openid_url = openid_url + '.dreamwidth.org'
        
        saso.make_pending_vote_entry(openid_url)
        
        # we're not using these parts of the example but I did not strip them
        # out on the theory that we might end up needing them for some reason
        #immediate = 'immediate' in self.query
        #use_sreg = 'use_sreg' in self.query
        #use_pape = 'use_pape' in self.query
        #use_stateless = 'use_stateless' in self.query
        immediate = 0
        use_sreg = 0
        use_pape = 0
        use_stateless = 0
        
        oidconsumer = self.getConsumer(stateless = use_stateless)
        try:
            request = oidconsumer.begin(openid_url)
        except consumer.DiscoveryFailure, exc:
            fetch_error_string = 'Error in discovery: %s' % (
                cgi.escape(str(exc[0])))
            self.render(fetch_error_string,
                        css_class='error',
                        form_contents=openid_url)
        else:
            if request is None:
                msg = 'No OpenID services found for <code>%s</code>' % (
                    cgi.escape(openid_url),)
                self.render(msg, css_class='error', form_contents=openid_url)
            else:
                # Then, ask the library to begin the authorization.
                # Here we find out the identity server that will verify the
                # user's identity, and get a token that allows us to
                # communicate securely with the identity server.
                if use_sreg:
                    self.requestRegistrationData(request)
                
                if use_pape:
                    self.requestPAPEDetails(request)
                
                trust_root = self.server.base_url
                #print 'trust_root is ' + trust_root
                return_to = self.buildURL('voting')
                #print 'return_to is ' + return_to
                if request.shouldSendRedirect():
                    redirect_url = request.redirectURL(
                        trust_root, return_to, immediate=immediate)
                    self.send_response(302)
                    self.send_header('Location', redirect_url)
                    self.writeUserHeader()
                    self.end_headers()
                else:
                    form_html = request.htmlMarkup(
                        trust_root, return_to,
                        form_tag_attrs={'id':'openid_message'},
                        immediate=immediate)
                    
                    self.wfile.write(form_html)
    
    def renderVoting(self):
        """Render the page header"""
        """Handle the redirect from the OpenID server."""
        
        oidconsumer = self.getConsumer()
        
        # Ask the library to check the response that the server sent
        # us. Status is a code indicating the response type. info is
        # either None or a string containing more information about
        # the return type.
        # url = 'http://'+self.headers.get('Host')+self.path
        # rax: hardcoding this for maximum bullshit
        # this makes me not just a bad programmer but a bad person
        url = 'http://autumnfox.akrasiac.org/saso/'+ self.path.strip('/')
        info = oidconsumer.complete(self.query, url)
        
        sreg_resp = None
        pape_resp = None
        css_class = 'error'
        display_identifier = info.getDisplayIdentifier()
        # There has to be a username.
        if not display_identifier:
            self.render('Please enter a Dreamwidth username.',
                        css_class='error', form_contents=('','','',''))
            return
        dwname = (display_identifier.split('.')[0]).split('//')[1]
        openid_url = dwname
        
        if saso.get_player_email(dwname) == 'player does not exist':
            self.render('Only partipants may vote.',
                        css_class='error', form_contents=('','','',''))
            return
        
        if not saso.check_pending_vote_entry(dwname):
            self.render('The software choked and lost your login name, sorry. Kick hurristat.',
                css_class='error', form_contents=(dwname,'','',''))
            return
        
        vote_option_string = ''
        
        if info.status == consumer.FAILURE and display_identifier:
            # In the case of failure, if info is non-None, it is the
            # URL that we were verifying. We include it in the error
            # message to help the user figure out what happened.
            fmt = "Verification of %s failed: %s"
            message = fmt % (cgi.escape(display_identifier),
                             info.message)
        elif info.status == consumer.SUCCESS:
            if voting_round == 1:
                if not saso.existing_voting_team_assignments(dwname):
                    saso.assign_voting_assignments(dwname)
                
                saso.remove_pending_voting_entry(dwname)
                
                vote_options = saso.get_vote_option_list(dwname)
                
                vote_option_string = str()
                
                for i in vote_options:
                    vote_option_string = vote_option_string + '\n<p>' + i + '</p>'
                vote_option_string = vote_option_string + '\n'
            elif voting_round == 2:
                saso.remove_pending_voting_entry(dwname)
                if not saso.player_vote_exists(dwname):
                    saso.create_entry_for_player(dwname)
                vote_option_string = '\n<p>akaashi keiji/bokuto koutarou</p>\n<p>bokuto koutarou/kuroo tetsurou</p>\n<p>daiya no ace</p>\n<p>imaizumi shunsuke/kinjou shingo</p>\n<p>imaizumi shunsuke/naruko shoukichi</p>\n<p>imaizumi shunsuke/sugimoto terufumi</p>\n<p>kageyama tobio/oikawa tooru</p>\n<p>kanzaki miki/miyahara</p>\n<p>kominato ryousuke/kuramochi youichi</p>\n<p>kuramochi youichi/miyuki kazuya</p>\n<p>kuroo tetsurou/sawamura daichi</p>\n<p>miyuki kazuya/oikawa tooru</p>\n<p>oikawa tooru/ushijima wakatoshi</p>\n<p>sawamura daichi/sugawara koushi</p>\n<p>the prince of tennis</p>\n' #this is the final round list, future me
            self.actuallyVotingPage(None, vote_option_string, openid_url)
	    return
        elif info.status == consumer.CANCEL:
            # cancelled
            message = 'Verification cancelled'
        elif info.status == consumer.SETUP_NEEDED:
            if info.setup_url:
                message = '<a href=%s>Setup needed</a>' % (
                    quoteattr(info.setup_url),)
            else:
                # This means auth didn't succeed, but you're welcome to try
                # non-immediate mode.
                message = 'Setup needed'
        else:
            # Either we don't understand the code or there is no
            # openid_url included with the error. Give a generic
            # failure message. The library should supply debug
            # information in a log.
            message = 'Verification failed.'
        
        self.render(message, css_class, display_identifier, sreg_data=sreg_resp, pape_Date=pape_resp)
    
    def actuallyVotingPage(self, form_contents, vote_option_string, openid_url):
        """Render the page header"""
        #self.setSessionCookie()
        #self.send_response(200)
        self.wfile.write('''\
<html>
<head>
    <title>
    SASO 2017 VOTING
    </title>

    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <meta http-equiv="refresh" content="50000" />
    <meta name="dcterms.rights" content="Website Coding (C) 2015-17 SASO Mod Team, 2014 HSWC Mod Team" />
    <link rel="shortcut icon" href="http://i.imgur.com/wBU1Jzp.png">
    
    <style type="text/css" media="all">

html, body {    
    font-family: Verdana,Arial,"Liberation Sans",sans-serif;
    color: #000;
    font-size: 11pt;
    background-color: #e5e4e5;
}

a:link,a:visited {
    color: #3c3c89;
    font-weight:bold;
    text-decoration: none;
}

a:hover {
    color: #4e5273;
    font-weight:bold;
    text-decoration: underline;
}

h1 {
    font-size: 18pt;
    text-transform: uppercase;
    color: #3c3c89;
    text-align: center;
}

.navigation {
    margin-left: auto;
    margin-right: auto; 
    text-align: center;
    border-top: 1px #4e5273 solid;
    width:50%;
    padding: 22px 0px 10px 0px;
}

.alert {
    border: 2px solid #e7dc2b;
    margin: 0px 10px 20px 0px;
    padding: 7px;
    background-color: #fff888;
    font-weight: bold;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
    width: 70%;
}

.error {
    border: 2px solid #ff0000;
    margin: 0px 10px 20px 0px;
    padding: 7px;
    background-color: #ffaaaa;
    font-weight: bold;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
    width: 70%;
}

form {
    width: 70%;
    background-color: #fff;
    padding: 20px;
    margin-left: auto;
    margin-right: auto;
    margin-top:1%;
    border-radius:10px;
    box-shadow:5px 5px #babad5;
}

.edit { 
    border: 2px #4e5273 solid;
    margin: 7px;
    padding: 7px;
    background-color: #f1f1f1;
    }

input, textarea {
    border: 1px solid black;
    background-color: #fff;
    margin: 3px 0px 0px 0px;
}

.field {
    font-weight:bold
    }

.descrip {
    font-size:10pt;
    color:#202020;
}
    </style>
</head>
<body>
    <h1>
    SASO 2017 VOTING FORM
    </h1>
<p class="navigation"><a href="http://autumnfox.akrasiac.org/saso/teams">Team Roster</a> | <a href="http://referees.dreamwidth.org/487.html">Mod Contact</a> | <a href="http://sportsanime.dreamwidth.org">Dreamwidth</a> | <a href="http://sportsanime.dreamwidth.org/750.html">Rules</a> | <a href="http://sportsanimeolympics.tumblr.com">Tumblr</a></p>
<p>Please read <a href="http://saso2017-r2.dreamwidth.org/7602.html">here</a> and choose your favorite three of the following choices. You are not allowed to vote for your own team's submission! </p>''' + vote_option_string + '''
<form method="GET" accept-charset="UTF-8" action=/saso/voteaccept>
<p>
    <span class="field">Vote 1:</span><br />
    <span class="descrip">Please enter your first vote</span><br />
    <input name="vote1" type="text" />
</p>
<p>
    <span class="field">Vote 2:</span><br />
    <span class="descrip">Please enter your second vote</span><br />
    <input name="vote2" type="text" />
</p>
<p>
    <span class="field">Vote 3:</span><br />
    <span class="descrip">Please enter your third vote</span><br />
    <input name="vote3" type="text" />
    
    <input name="username" type="hidden" value="''' + openid_url + '''"/>
</p>
<input type="submit" value="Submit">
</form>
<p style="text-align:center"><img src="http://i.imgur.com/98vfANt.png" alt="SPORTS!" /></p>
</body>
</html>
''')
    
    def acceptMessage(self):
        response = ''
        vote1 = str(self.query.get('vote1'))
        vote2 = str(self.query.get('vote2'))
        vote3 = str(self.query.get('vote3'))
        vote1 = vote1.strip()
        vote2 = vote2.strip()
        vote3 = vote3.strip()
        print vote1 + ' ' + vote2 + ' ' + vote3
        openid_url = self.query.get('username')
        player_team = saso.get_current_team(openid_url)
        
        if voting_round == 1:
            valid_teams = saso.get_vote_option_list(openid_url)
            if not vote1 in valid_teams or not vote2 in valid_teams or not vote3 in valid_teams:
                response = 'not all fields have been entered correctly! <a href="http://autumnfox.akrasiac.org/saso/vote">please try again here</a>'
            elif vote1 == vote2 or vote1 == vote3 or vote2 == vote3:
                response = 'all votes must be for different entries! <a href="http://autumnfox.akrasiac.org/saso/vote">please try again here</a>'
            else:
                response = 'your votes were received! thank you for voting!'
                saso.enter_votes(openid_url, vote1, vote2, vote3)
        elif voting_round == 2:
            valid_teams = ['akaashi keiji/bokuto koutarou', 'bokuto koutarou/kuroo tetsurou', 'daiya no ace', 'imaizumi shunsuke/kinjou shingo', 'imaizumi shunsuke/naruko shoukichi', 'imaizumi shunsuke/sugimoto terufumi', 'kageyama tobio/oikawa tooru', 'kanzaki miki/miyahara', 'kominato ryousuke/kuramochi youichi', 'kuramochi youichi/miyuki kazuya', 'kuroo tetsurou/sawamura daichi', 'miyuki kazuya/oikawa tooru', 'oikawa tooru/ushijima wakatoshi', 'sawamura daichi/sugawara koushi', 'the prince of tennis'] #update this for the final round of voting
            if not vote1 in valid_teams or not vote2 in valid_teams or not vote3 in valid_teams:
                response = 'not all fields have been entered correctly! <a href="http://autumnfox.akrasiac.org/saso/vote">please try again here</a>'
            elif vote1 == player_team or vote2 == player_team or vote3 == player_team:
                response = 'you cannot vote for your own team! <a href="http://autumnfox.akrasiac.org/saso/vote">please try again here</a>'
            elif vote1 == vote2 or vote1 == vote3 or vote2 == vote3:
                response = 'all votes must be for different entries! <a href="http://autumnfox.akrasiac.org/saso/vote">please try again here</a>'
            else:
               response = 'your votes were received! thank you for voting!'
               saso.enter_votes(openid_url, vote1, vote2, vote3)
        self.wfile.write('''\
<html>
<head>
    <title>
    SASO 2017 VOTING
    </title>

    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <meta http-equiv="refresh" content="50000" />
    <meta name="dcterms.rights" content="Website Coding (C) 2015-17 SASO Mod Team, 2014 HSWC Mod Team" />
    <link rel="shortcut icon" href="http://i.imgur.com/wBU1Jzp.png">
    
    <style type="text/css" media="all">

html, body {    
    font-family: Verdana,Arial,"Liberation Sans",sans-serif;
    color: #000;
    font-size: 11pt;
    background-color: #e5e4e5;
}

a:link,a:visited {
    color: #3c3c89;
    font-weight:bold;
    text-decoration: none;
}

a:hover {
    color: #4e5273;
    font-weight:bold;
    text-decoration: underline;
}

h1 {
    font-size: 18pt;
    text-transform: uppercase;
    color: #3c3c89;
    text-align: center;
}

.navigation {
    margin-left: auto;
    margin-right: auto; 
    text-align: center;
    border-top: 1px #4e5273 solid;
    width:50%;
    padding: 22px 0px 10px 0px;
}

.alert {
    border: 2px solid #e7dc2b;
    margin: 0px 10px 20px 0px;
    padding: 7px;
    background-color: #fff888;
    font-weight: bold;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
    width: 70%;
}

.error {
    border: 2px solid #ff0000;
    margin: 0px 10px 20px 0px;
    padding: 7px;
    background-color: #ffaaaa;
    font-weight: bold;
    text-align: center;
    margin-left: auto;
    margin-right: auto;
    width: 70%;
}

form {
    width: 70%;
    background-color: #fff;
    padding: 20px;
    margin-left: auto;
    margin-right: auto;
    margin-top:1%;
    border-radius:10px;
    box-shadow:5px 5px #babad5;
}

.edit { 
    border: 2px #4e5273 solid;
    margin: 7px;
    padding: 7px;
    background-color: #f1f1f1;
    }

input, textarea {
    border: 1px solid black;
    background-color: #fff;
    margin: 3px 0px 0px 0px;
}

.field {
    font-weight:bold
    }

.descrip {
    font-size:10pt;
    color:#202020;
}
    </style>
</head>
<body>

    <h1>
    SASO 2017 VOTING FORM
    </h1>

<p class="navigation"><a href="http://autumnfox.akrasiac.org/saso/">Sign Up Form</a> | <a href="http://autumnfox.akrasiac.org/saso/teams">Team Roster</a> | <a href="http://referees.dreamwidth.org/487.html">Mod Contact</a> | <a href="http://sportsanime.dreamwidth.org/">Dreamwidth</a> | <a href="http://sportsanime.dreamwidth.org/750.html">Rules</a> and <a href="http://sportsanime.dreamwidth.org/839.html">FAQ</a> | <a href="http://sportsanimeolympics.tumblr.com">Tumblr</a></p>

''' + response + '''

<p style="text-align:center"><img src="http://i.imgur.com/98vfANt.png" alt="SPORTS!" /></p>

</body>
</html>
''')

def main(host, port, data_path, weak_ssl=False):
    # Instantiate OpenID consumer store and OpenID consumer. If you
    # were connecting to a database, you would create the database
    # connection and instantiate an appropriate store here.
    if data_path:
        store = filestore.FileOpenIDStore(data_path)
    else:
        store = memstore.MemoryStore()
    
    if weak_ssl:
        setDefaultFetcher(Urllib2Fetcher())
    
    addr = (host, port)
    server = OpenIDHTTPServer(store, addr, OpenIDRequestHandler)
    
    print 'Server running at:'
    print server.base_url
    server.serve_forever()

if __name__ == '__main__':
    host = 'localhost'
    port = 8600
    weak_ssl = False
    
    try:
        import optparse
    except ImportError:
        pass # Use defaults (for Python 2.2)
    else:
        parser = optparse.OptionParser('Usage:\n %prog [options]')
        parser.add_option(
            '-d', '--data-path', dest='data_path',
            help='Data directory for storing OpenID consumer state. '
            'Setting this option implies using a "FileStore."')
        parser.add_option(
            '-p', '--port', dest='port', type='int', default=port,
            help='Port on which to listen for HTTP requests. '
            'Defaults to port %default.')
        parser.add_option(
            '-s', '--host', dest='host', default=host,
            help='Host on which to listen for HTTP requests. '
            'Also used for generating URLs. Defaults to %default.')
        parser.add_option(
            '-w', '--weakssl', dest='weakssl', default=False,
            action='store_true', help='Skip ssl cert verification')
        
        options, args = parser.parse_args()
        if args:
            parser.error('Expected no arguments. Got %r' % args)
        
        host = options.host
        port = options.port
        data_path = options.data_path
        weak_ssl = options.weakssl
    
    main(host, port, data_path, weak_ssl)
