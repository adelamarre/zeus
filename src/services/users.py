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
from src.services.userAgents import UserAgentManager


class UserManager:
    def __init__(self, basePath):
        self.basePath = basePath
        self.emailManager = EmailManager(basePath=basePath)
        self.userAgentManager = UserAgentManager(basePath=basePath)
        self.users = []

    def createRandomUser(self, proxy, application):
        randomEmailData = self.emailManager.getRandomEmail()
        now = datetime.now()
        return {
            'application': application,
            'email': randomEmailData['email'],
            'password': ''.join(choice(ascii_letters + digits) for _ in range(randint(8, 14))),
            'displayName': '%s %s' % (randomEmailData['firstname'], randomEmailData['lastname']),
            'proxy': proxy,
            'userAgent': self.userAgentManager.getRandomUserAgent(),
            'windowSize': choice(['1920,1080', '1024,768', '1680,1050', '1344,840','1024,640']),
            'createdAt': now.strftime("%d/%m/%Y %H:%M:%S") 
        }