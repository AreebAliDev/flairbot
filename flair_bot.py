"""Flair bot."""
import sys
import os
import re
import codecs
import csv
from time import gmtime, strftime
import praw
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser


class FlairBot:
    """Flair bot."""

    def __init__(self):
        """Initial setup."""

        self.conf = ConfigParser()
        self.flairs = {}
        self.reddit = None

        os.chdir(sys.path[0])
        if os.path.exists('conf.ini'):
            self.conf.read('conf.ini')
        else:
            raise FileNotFoundError('Config file, conf.ini, was not found.')

        if self.conf.get('log', 'logging') == 'False':
            self.logging = False
        else:
            self.logging = True

        self.login()

    def login(self):
        """Log in via script/web app."""

        app_id = self.conf.get('app', 'app_id')
        app_secret = self.conf.get('app', 'app_secret')
        user_agent = self.conf.get('app', 'user_agent')

        if self.conf.get('app', 'auth_type') == 'webapp':
            token = self.conf.get('auth-webapp', 'token')
            self.reddit = praw.Reddit(client_id=app_id,
                                      client_secret=app_secret,
                                      refresh_token=token,
                                      user_agent=user_agent)
        else:
            username = self.conf.get('auth-script', 'username')
            password = self.conf.get('auth-script', 'passwd')
            self.reddit = praw.Reddit(client_id=app_id,
                                      client_secret=app_secret,
                                      username=username,
                                      password=password,
                                      user_agent=user_agent)

        self.get_flairs()

    def get_flairs(self):
        """Read flairs from CSV."""

        with open('flair_list.csv') as csvf:
            csvf = csv.reader(csvf)
            flairs = {}
            for row in csvf:
                if len(row) == 2:
                    flairs[row[0]] = row[1]
                else:
                    flairs[row[0]] = None

        self.flairs = flairs
        self.fetch_pms()

    def fetch_pms(self):
        """Grab unread PMs."""

        target_sub = self.conf.get('subreddit', 'name')
        valid = r'[A-Za-z0-9_-]+'
        subject = self.conf.get('subject', 'subject')
        for msg in self.reddit.inbox.unread():
            author = str(msg.author)
            valid_user = re.match(valid, author)
            if msg.subject == subject and valid_user:
                self.process_pm(msg, author, target_sub)
        sys.exit()

    def process_pm(self, msg, author, target_sub):
        """Process unread PM."""

        author = str(msg.author) #get the author
        body = msg.body.split(' ') #split the PM by spaces into an array
        csscls = body[0] #the class will always be the first entry in the array
        if len(body) > 1:
            txt = (" ").join(body[1:])
             #if the array is more than one item long (i.e there is custom text after the class name)
             #then we join the remainder (from array position 1 - [1:]) into a string
        else:
            txt = '' #otherwise there is no custom text and we set it to empty
        subreddit = self.reddit.subreddit(target_sub)
        subreddit.flair.set(author, txt, csscls)
        if self.logging:
            self.log(author, txt, csscls)
        msg.mark_read()

    @staticmethod
    def log(user, text, cls):
        """Log applied flairs to file."""

        with codecs.open('log.txt', 'a', 'utf-8') as logfile:
            time_now = strftime("%Y-%m-%d %H:%M:%S", gmtime())
            log = 'user: ' + user
            log += ' | class(es): ' + cls
            if len(text):
                log += ' | text: ' + text
            log += ' @ ' + time_now + '\n'
            logfile.write(log)

FlairBot()
