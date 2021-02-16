
import sys
import os
import json
from datetime import datetime
from time import sleep
from random import randint
from os import path
from ...services.users import UserManager
from ...services.proxies import ProxyManager, PROXY_FILE_REGISTER
from ...services.userAgents import UserAgentManager
from ...services.tasks import TaskContext
from ...services.console import Console
from ...services.questions import Question
from .Spotify import Adapter
import traceback

def runner(uid, context: TaskContext, accountFile, user, mode):
    
    context.console.log('Task %d start registering user %s ...' % (uid, user['email']))
    
    context.setTaskState('Signup: %s' % user['email'])
    
    def writeUser():
        with context.locks['accounts']:
            with open(accountFile,'a') as f:
                f.write(json.dumps(user) + '\n')
    
    browser = False
      
    if context.config.DRY_RUN:
        sleep(randint(20, 30))
        if randint(0,20):
            writeUser()
    else:
        try:
            if mode == 'regular':
                browser = context.driverManager.getDriver('chrome', uid, user)
                if browser:
                    spotify = Adapter(browser, context)
                    result = spotify.register(user)
                    browser.quit()
            else:
                spotify = Adapter(None, context)
                result = spotify.registerApi(user)

            if result:
                writeUser()
                context.console.success('Registration success for %s' % user['email'])
            else:
                context.console.error('Registration failed for %s' % user['email'])
            
        except:
            context.console.error('Register task error: %s' % traceback.format_exc())
            try:
                if browser:
                    browser.quit()
            except:
                pass


class Scenario:
    def __init__(self, console: Console):
        self.tempFile = (os.path.dirname(__file__) or '.') + '/../_' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")+'.tmp'
        self.console = console

    def init(self):
        try:
            self.mode = app = Question().choice('Wich mode:', {
                'api': {
                    'displayName': 'Api',
                    'enable': True,
                },
                'regular': {
                    'displayName': 'Regular',
                    'enable': True,
                },
            })
            self.nbrAccount = int(input('How much free account you want ?'))
        except:
            return False
        return True

    def getTasks(self):
        self.console.log('Scenario start')
        pm = ProxyManager(PROXY_FILE_REGISTER)
        uam = UserAgentManager()
        um = UserManager(self.console)
        tasks = []
        try:
            for nbr in range(self.nbrAccount):
                proxy = pm.getRandomProxy()
                userAgent = uam.getRandomUserAgent()
                tasks.append({
                    'timeout': 300,
                    'user': um.createRandomUser(proxy, userAgent, 'Spotify'),
                    'accountFile': self.tempFile,
                    'mode': self.mode,
                })
        except:
            self.console.error('Scenario error getTasks():', sys.exc_info())
        return tasks

    def getRunner(self):
        return runner

    def finish(self):
        self.console.log('Scenario finish')
        result = []
        try:
            if path.exists(self.tempFile):
                with open(self.tempFile,'r') as t:
                    for line in t:
                        try:
                            user = json.loads(line)
                            result.append(user)
                        except:
                            pass
            else:
                self.console.warning('Users temporary file not found !')            
        
            accountFile = (os.path.dirname(__file__) or '.') + '/../../../Sportify_Free_Account_' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")+'.json'
            with open(accountFile, 'w') as f:
                json.dump(result, f)
            os.remove(self.tempFile)
        except:
            self.console.exception()
        
        