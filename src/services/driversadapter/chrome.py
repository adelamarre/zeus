
import seleniumwire
from src.services.console import Console
from selenium.webdriver.chrome.options import Options
#from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from zipfile import ZipFile
from selenium.webdriver.chrome.service import Service

#from selenium import webdriver
from random import randint
import os
import shutil
from tempfile import mkdtemp
from time import sleep
from src.services.bash import version
from traceback import format_exc
from platform import system
from src.services.proxies import Proxy

seleniumWire = True
if not seleniumwire:
    from selenium import webdriver
else:
    from seleniumwire import webdriver 

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Chrome Proxy",
    "permissions": [
        "proxy",
        "tabs",
        "unlimitedStorage",
        "storage",
        "<all_urls>",
        "webRequest",
        "webRequestBlocking"
    ],
    "background": {
        "scripts": ["background.js"]
    },
    "minimum_chrome_version":"22.0.0"
}
"""



class ChromeDriverAdapter:
    def __init__(self, console: Console, startService=False) -> None:
        self.console = console
        if startService:
            self.service = Service(executable_path='/usr/local/bin/chromedriver')
            self.service.start()
        else:
            self.service = None

        self.drivers = []
        self.userDataDir = []
        
        bv = version('google-chrome')
        dv = version('chromedriver')
        self.driverVersion  = '%s %s' % (dv[0], dv[1])
        self.browserVersion = '%s%s %s' %  (bv[0], bv[1], bv[2])
        sleep(1)

    def purge(self) -> None:
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        for userdatadir in self.userDataDir:
            try:
                shutil.rmtree(path=userdatadir, ignore_errors=True)
            except:
                pass

        #self.service.stop()

    def getNewInstance(self, uid, user, proxy=None, headless=False) -> webdriver:
        pluginfile = None
        try:
            if proxy is None:
                if 'proxy' in user:
                    proxy = user['proxy']

            options = Options()
            options.add_argument('--no-sandbox')  
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument('media.eme.enabled')
            options.add_argument("--disable-gpu")
            options.add_argument('--disable-popup-blocking')
            options.add_argument("--disable-blink-features")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument('--ignore-certificate-errors-spki-list')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')

            options.add_argument("--enable-features=NetworkServiceInProcess")
            options.add_argument("--disable-features=NetworkService") 
            options.add_argument("--disable-browser-side-navigation") 
            options.add_argument("--aggressive-cache-discard")
            options.add_argument("--disable-cache")
            options.add_argument("--disable-application-cache"); 
            options.add_argument("--disable-offline-load-stale-cache")
            options.add_argument("--disk-cache-size=0")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.page_load_strategy = 'normal'
            #options.add_argument("--window-position=-32000,-32000");
            #options.add_argument("--log-path=" + (os.path.dirname(__file__) or '.') + "/../chrome.log")
            #options.add_argument("--log-level=3")
            #options.add_argument("--single-process")
            
            

            
            
            
            
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            
            userDataDir = mkdtemp()
            self.userDataDir.append(userDataDir)
            options.add_argument('--user-data-dir=%s' % userDataDir)

            if 'windowSize' in user:
                options.add_argument("--window-size=%s" % user['windowSize'])

            if headless:
                options.add_argument("--headless")
            
            # Set user agent if available
            if 'userAgent' in user:
                options.add_argument('user-agent=%s' % user['userAgent'])

            desired_capabilities = DesiredCapabilities.CHROME.copy()
            soptions = {}
            if seleniumWire:
                soptions = {
                    'ignore_http_methods': [],
                    'connection_timeout': None, 
                    'verify_ssl': False,
                }
                if proxy:
                    proxyUrl = Proxy.getUrl(proxy)
                    soptions['proxy'] = {
                        'https': '%s' % proxyUrl,
                        'http': '%s' % proxyUrl,
                        'no_proxy': 'localhost,127.0.0.1',
                    }
            else:
                if proxy:
                    proxyUrl = Proxy.getUrl(proxy)
                    desired_capabilities['proxy'] = {
                        'proxyType': 'manual',
                        'httpProxy': '%s' % proxyUrl,
                        'sslProxy': '%s' % proxyUrl,
                        'no_proxy': 'localhost,127.0.0.1',
                    }

            
            #incognito argument disable the use of the proxy, DO NOT SET ! 
            #options.add_argument("--incognito")
            

            
            
            

            
            # add a proxy if available
            #if proxy:
            #    pluginfile = self.buildChromeExtension(proxy)
            #    options.add_extension(pluginfile)

            #prefs: {
            #    protocol_handler: {
            #        excluded_schemes: {
            #            sms: false,
            #        },
            #    },
            #},
            
            
            #Instantiate the driver
            if self.service:
                driver = webdriver.Remote(self.service.service_url, desired_capabilities=desired_capabilities, options=options, seleniumwire_options=soptions)
            else:
                driver = webdriver.Chrome(options=options, desired_capabilities=desired_capabilities, seleniumwire_options=soptions)
            #driver = webdriver.Remote(self.service.service_url, desired_capabilities=desired_capabilities, options=options)
            
            #Make webdriver = undefined
            script = '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            })
            '''
            driver.execute_script(script)
            
            #if proxy:
            #    def requestInterceptor(request):
            #        request.headers['Zeus-proxy': '%s:%s:%s:%s' % (proxy['host', proxy['port'], proxy['username'], proxy['password']])]
            #    driver.request_interceptor = requestInterceptor

            #if pluginfile:
            #    os.remove(pluginfile)
            #    pluginfile = None

            return {
                'driver': driver,
                'userDataDir': userDataDir,
            }
        except:
            self.console.exception()
            if pluginfile:
                os.remove(pluginfile)
            return None
    
    def buildChromeExtension(self, proxy):
        pluginfile = 'proxy_auth_plugin_%d.zip' % randint(100000, 999999)
        background_js = ''
        if len(proxy) == 4:
            background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
          },
          bypassList: ["localhost"]
        },
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

function callbackFn(details) {
    return {
        authCredentials: {
            username: "%s",
            password: "%s"
        }
    };
}

chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
);
""" % (proxy['host'], proxy['port'], proxy['username'], proxy['password'])
        elif len(proxy) == 2:
            background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "http",
            host: "%s",
            port: parseInt(%s)
          },
          bypassList: ["localhost"]
        },
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
""" % (proxy['host'], proxy['port'])

        with ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json)
            zp.writestr("background.js", background_js)
        return pluginfile
