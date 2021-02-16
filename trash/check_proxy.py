
import os
import random
from src.services.console import Console
import sys
import traceback
from ...services.drivers import DriverManager
from ...services.users import UserManager
from ...services.userAgents import UserAgentManager
from ...services.proxies import ProxyManager
from ...services.threads import TaskContext
from .Spotify import Adapter
from time import sleep
from ...services.proxies import PROXY_FILE_LISTENER, PROXY_FILE_REGISTER
from ...services.questions import Question

__DIR__ = (os.path.dirname(__file__) or '.')

USERS_FILE = __DIR__ + '/data/users.txt'

def runner(uid, context: TaskContext, user, proxy):
    context.console.log('Check proxy runner #%d running...' % uid)
    try:
        #browser = context.driverManager.getChromeDriver(uid, user)
        browser = context.driverManager.getDriver('chrome', uid, user, proxy, context.config.WEBDRIVER_HEADLESS)
        spotify = Adapter(browser, context)
        sleep(2)
        context.console.log('Task %d is registering user %s ...' % (uid, user['email']))
    
        info = spotify.getClientInfo('http://35.180.119.212')
        if 'server' in info:        
            context.setTaskState('Ip: %s' % info['server']['REMOTE_ADDR'])
            context.console.success('[#%3d] Browser identity: %s, %s' % (uid, info['server']['REMOTE_ADDR'], info['server']['HTTP_USER_AGENT']))
        else:
            context.console.error('Check proxy error: getClientInfo return :\n%s' % info['raw'])
        sleep(5)
    except:
        context.console.log('Runner %d error: %s' % (uid, traceback.format_exc()))
    try:
        browser.quit()   
    except:
        pass
   
class Scenario:
    def __init__(self, console: Console):
        self.console = console
    def init(self):
        try:
            self.proxylist = Question().choice('Wich proxy list ?', {
                'register': {
                    'displayName': 'Register',
                },
                'listener': {
                    'displayName': 'Listener',
                }
            })
            self.nbrTests = int(input('How much test would you like to do ?'))
        except:
            return False
        return True

    def getTasks(self):
        
        tasks = []
        pm = None
        if self.proxylist == 'register':    
            pm = ProxyManager(PROXY_FILE_REGISTER)
        elif self.proxylist == 'listener':
            pm = ProxyManager(PROXY_FILE_LISTENER)
        
        um = UserManager(self.console)
        ua = UserAgentManager()

        for index in range(self.nbrTests):
            user = um.createRandomUser(pm.getRandomProxy(), ua.getRandomUserAgent(), 'Spotify')
            tasks.append({
                'user': user,
                'proxy': pm.getRandomProxy(),
            })
        return tasks
        
    def getRunner(self):
        return runner
    
    def finish(self):
        pass

