from .console import Console
from time import sleep
from random import randint
from .driversadapter.chrome import ChromeDriverAdapter

class DriverManager:
    def __init__(self, console: Console):
        self.chrome = ChromeDriverAdapter(console)
        self.console = console
    

    def getDriver(self, type, uid, user, proxy=None, headless=False):
        driver = None
        tryCount = 3
        while True:
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
                if tryCount:
                    tryCount -= 1
                    sleep(5)
                else:
                    sleep(randint(3,6))
                    self.console.exception()
                    break
        return driver    

    def purge(self):
        self.chrome.purge()
    