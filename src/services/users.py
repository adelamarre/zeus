import os
from datetime import datetime
import json
from typing import Dict, List
from .emails import EmailManager
from random import randint, choice
from string import ascii_letters, ascii_lowercase, digits
from .console import Console
from .questions import Question
import sys

__DIR__ = (os.path.dirname(__file__) or '.')

USERS_FILE = __DIR__ + '/../../data/users.json'


class UserManager:
    def __init__(self, console: Console):
        self.console = console
        self.emailManager = EmailManager()
        self.users = []


    def getRandomUser(self):
        if len(self.users):
            return choice(self.users)
            
    def getUserFilename(self):
        import glob, os
        
        choice = {}
        for file in glob.glob((os.path.dirname(__file__) or '.') + '/../../Spo*_*.json'):
            head, tail = os.path.split(file)
            choice[file] = {
                'displayName': tail
            }
        if len(choice) > 0:
            return Question().choice('Select the user file :', choice)
        else:
            return None

    def getUsers(self) -> List:
        userFile = self.getUserFilename()
        if not userFile:
            sys.exit(0)
        try:
            with open(userFile, 'r') as usersFile:
                self.users = json.load(usersFile)
        except:
            self.console.warning('Could not find %s in /data folder !' % userFile)

        #print('Found %d users' % len(self.users))
        return self.users

    def createRandomUser(self, proxy, userAgent, application):
        randomEmailData = self.emailManager.getRandomEmail()

        now = datetime.now()
        return {
            'application': application,
            'email': randomEmailData['email'],
            'password': ''.join(choice(ascii_letters + digits) for _ in range(randint(8, 14))),
            'displayName': '%s %s' % (randomEmailData['firstname'], randomEmailData['lastname']),
            'proxy': proxy,
            'userAgent': userAgent,
            'windowSize': choice(['1920,1080', '1024,768', '1680,1050', '1344,840','1024,640']),
            'createdAt': now.strftime("%d/%m/%Y %H:%M:%S") 
        }