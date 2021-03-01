import sys
import os
import random
from .files import FileManager



FIRSTNAME_DATA_FILE = '/firstname.txt'
LASTNAME_DATA_FILE = '/lastname.txt'
DOMAIN_DATA_FILE = '/domain.txt'


class EmailManager:
    def __init__(self, basePath):
        fileManager = FileManager(basePath=basePath)
        self.firstnames = fileManager.loadTextFile(FIRSTNAME_DATA_FILE)
        self.lastnames = fileManager.loadTextFile(LASTNAME_DATA_FILE)
        self.domains = fileManager.loadTextFile(DOMAIN_DATA_FILE)
    
    def getRandomEmail(self, addUid=random.choice([False, True])):
        uid = ''
        if addUid:
            uid = str(random.randint(100, 999))
        firstname = random.choice(self.firstnames)
        lastname = random.choice(self.lastnames)

        email = '{firstname}{separator}{lastname}{uid}@{domain}'.format(
            uid=uid,
            firstname=firstname,
            lastname=lastname,
            domain=random.choice(self.domains),
            separator=random.choice(['.', '-', '_', ''])
        )
        return {
            'email': email,
            'firstname': firstname,
            'lastname': lastname
        }

