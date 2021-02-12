from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common import desired_capabilities
from seleniumwire import webdriver
from .console import Console
import requests
import sys
from zipfile import ZipFile
import os
import platform
from selenium.webdriver import Proxy
from threading import Lock
import shutil
import phantomjs
import base64
import codecs

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
                break;
            except:
                if tryCount:
                    tryCount -= 1
                    sleep(5)
                else:
                    sleep(randint(3,6))
                    self.console.exception()
                    break;
        return driver    

    def purge(self):
        self.chrome.purge()
    