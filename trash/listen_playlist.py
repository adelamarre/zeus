
import os
import traceback
from random import randint
from ...services.threads import TaskContext
from ...services.drivers import DriverManager
from ...services.users import UserManager
from ...services.proxies import ProxyManager
from ...services.console import Console
from .Spotify import Adapter
from time import sleep
from ...services.proxies import PROXY_FILE_LISTENER

__DIR__ = (os.path.dirname(__file__) or '.')

USERS_FILE = __DIR__ + '/data/users.txt'

def runner(uid, context: TaskContext, user, playlist):
    #print('runner #%d running...' % id, user, proxy, userAgent
    browser = None
    try:
        if context.config.DRY_RUN:
            sleep(randint(20, 30))
            return
            

        browser = context.driverManager.getDriver('chrome', uid, user)
        spotify = Adapter(browser, context)
        print ('Runner %d start listening for user %s ...' % (uid, user['email']))
        context.setTaskState('Login...')
        if spotify.login(user['email'], user['password']):
            spotify.playPlaylist(playlist, 90, 110)
        
    except KeyboardInterrupt:
        pass
    
    except:
        context.console.error('Listener #%d error: %s' % (uid, traceback.format_exc()))
    
    context.setTaskState('Quit...')
    if browser:
        try:
            browser.quit()
        except:
            pass
    try:
        context.driverManager.purge(uid)
    except:
        pass    

class Scenario:
    def __init__(self, console: Console):
        self.console = console
        
    
    def init(self):
        try:
            self.playlist = input('Wich play list to listen ? (url) :')
            if self.playlist == '':
                return False
        except:
            return False
        

       

    def getTasks(self):
        tasks = []    
        pm = ProxyManager(PROXY_FILE_LISTENER)
        users = UserManager(self.console).getUsers()
        for user in users:
            user['proxy'] = pm.getRandomProxy()
            tasks.append({
                'timeout': 330,
                'user': user,
                'playlist': self.playlist
            })
        return tasks

    def getRunner(self):
        return runner

    def finish(self):
        pass
