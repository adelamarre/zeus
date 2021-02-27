from .console import Console
from time import sleep
from random import randint
from .driversadapter.chrome import ChromeDriverAdapter
from multiprocessing import Event, synchronize

class DriverManager:
    def __init__(self, console: Console, shutdownEvent: synchronize.Event, startService=False):
        self.chrome = ChromeDriverAdapter(console=console, startService=startService)
        self.console = console
        self.shutdownEvent = shutdownEvent
    
    def getDriverVersion(self, type):
        if type == 'chrome':
            return self.chrome.driverVersion
        return 'Unknown'

    def getBrowserVersion(self, type):
        if type == 'chrome':
            return self.chrome.browserVersion
        return 'Unknown'

    def getDriver(self, type, uid, user, proxy=None, headless=False):
        driver = None
        tryCount = 3
        while not self.shutdownEvent.is_set() :
            try:
                if type == 'chrome':
                    #driver = self.getChromeDriver(uid, user, proxy, headless)
                    driver = self.chrome.getNewInstance(uid, user, proxy, headless)
                elif type == 'firefox':
                    pass
                else:
                    driver = self.chrome.getNewInstance(uid, user, proxy, headless)
                if driver:
                    break
                else:
                    raise Exception("getDriver return None")    
            except:
                sleep(1)
                if tryCount:
                    tryCount -= 1
                else:
                    self.console.exception()
                    break
        return driver    
    
    def getServiceUrl(self, type):
        if type == 'chrome':
            return self.chrome.getServiceUrl()

    def purge(self):
        self.chrome.purge()
    