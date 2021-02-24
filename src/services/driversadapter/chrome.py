from src.services.console import Console
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from zipfile import ZipFile
from selenium.webdriver.chrome.service import Service
from shutil import rmtree
from random import randint
import os
import shutil
from tempfile import mkdtemp
from time import sleep
from src.services.bash import version
from traceback import format_exc
from platform import system
from src.services.proxies import Proxy
from os import path
seleniumWire = False
from selenium import webdriver
from seleniumwire import webdriver as webdriverwire 

manifest_json = """
{
    "version": "1.0.0",
    "manifest_version": 2,
    "name": "Slither.io",
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
        "scripts": ["background.js"],
        "persistent": true
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
        self.extensionDir = (path.dirname(__file__) or '.') + ('/../../../temp/extension/')
        try:
            os.makedirs(self.extensionDir)
        except:
            pass
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
            options.add_argument('--disable-setuid-sandbox')  
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument('media.eme.enabled')
            options.add_argument("--disable-gpu")
            options.add_argument('--disable-popup-blocking')
            options.add_argument("--disable-blink-features")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument('--ignore-certificate-errors-spki-list')
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--ignore-ssl-errors')

            #options.add_argument("--enable-features=NetworkServiceInProcess")
            #options.add_argument("--disable-features=NetworkService") 
            #options.add_argument("--disable-browser-side-navigation") 
            #options.add_argument("--aggressive-cache-discard")
            #options.add_argument("--disable-cache")
            #options.add_argument("--disable-application-cache"); 
            #options.add_argument("--disable-offline-load-stale-cache")
            #options.add_argument("--disk-cache-size=0")
            #options.add_argument("--disable-features=VizDisplayCompositor")
            options.page_load_strategy = 'normal'
            #options.add_argument("--window-position=-32000,-32000");
            #options.add_argument("--log-path=" + (os.path.dirname(__file__) or '.') + "/../chrome.log")
            options.add_argument("--log-level=3")
            #options.add_argument("--disable-logging")
            #options.add_argument("--disable-in-process-stack-traces");
            #options.add_argument("--single-process")
            #options.add_argument("--disable-arc-cpu-restriction")
            #options.add_argument("--disable-background-networking")
            #options.add_argument("--disable-breakpad")
            #options.add_argument("--disable-component-extensions-with-background-pages")
            #options.add_argument("--disable-crash-reporter")
            
            

            
            
            
            
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
            if headless:
                soptions = {
                    'ignore_http_methods': ['GET', 'PUT', 'OPTION', 'POST'],
                    'connection_timeout': None, 
                    'verify_ssl': False,
                    #'backend': 'mitmproxy',
                    #'mitm_confdir': (path.dirname(__file__) or '.') + '/../../../.mitmproxy',
                    #'mitm_ssl_insecure': True,
                    #'mitm_upstream_cert': True,
                    #'mitm_add_upstream_certs_to_client_chain': True,
                    #'mitm_keep_host_header': True,
                    #'mitm_console_eventlog_verbosity': 'error',
                    'suppress_connection_errors': True
                }
                if proxy:
                    soptions['proxy'] = {
                        'https': '%s' % Proxy.getUrl(proxy, 'https'),
                        'http': '%s' % Proxy.getUrl(proxy, 'http'),
                        'no_proxy': 'localhost,127.0.0.1',
                    }
            else:
                if proxy:

                    pluginfile = self.buildChromeExtension(proxy)
                    options.add_extension(pluginfile)
                    # IMPORTANT !!
                    # Without this argument the proxy credential windows will popup
                    # and block the driver
                    options.add_argument('--google-base-url=http://localhost')

                    #proxyUrl = Proxy.getUrl(proxy, 'https')
                    #desired_capabilities['proxy'] = {
                    #    'proxyType': 'manual',
                    #    'httpProxy': '%s' % proxyUrl,
                    #    'sslProxy': '%s' % proxyUrl,
                    #    'no_proxy': 'localhost,127.0.0.1',
                    #}

            
            
            #Instantiate the driver
            if self.service:
                if headless:
                    driver = webdriverwire.Remote(
                        self.service.service_url,
                        desired_capabilities=desired_capabilities,
                        options=options,
                        seleniumwire_options=soptions
                    )
                else:
                    driver = webdriver.Remote(
                        self.service.service_url,
                        desired_capabilities=desired_capabilities,
                        options=options
                    )
            else:
                if headless:
                    #self.console.log('Start Chrome driver (%s)' % (("screen", 'headless')[headless]))
                    driver = webdriverwire.Chrome(
                        options=options,
                        desired_capabilities=desired_capabilities,
                        seleniumwire_options=soptions,
                    )
                else:
                    driver = webdriver.Chrome(
                        options=options,
                        desired_capabilities=desired_capabilities,
                    )
            
            #Make webdriver = undefined
            # When headless this property is added to navigator by chrome
            script = '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            '''
            driver.execute_script(script)
            
            #if proxy:
            #    def requestInterceptor(request):
            #        request.headers['Zeus-proxy': '%s:%s:%s:%s' % (proxy['host', proxy['port'], proxy['username'], proxy['password']])]
            #    driver.request_interceptor = requestInterceptor

            #if pluginfile:
            #    os.remove(pluginfile)
            #    pluginfile = None
            if pluginfile:
                os.remove(pluginfile)
            return {
                'driver': driver,
                'userDataDir': userDataDir,
            }
        except:
            self.console.exception()
        
        if pluginfile:
                try:
                    os.remove(pluginfile)
                except:
                    pass
        if userDataDir:
                rmtree(path=userDataDir, ignore_errors=True)
        return None
        
    
    def buildChromeExtension(self, proxy):
        pluginfile = self.extensionDir + ('proxy_auth_plugin_%d.zip' % randint(100000, 999999))
        background_js = ''
        if len(proxy) == 5:
            background_js = """
var config = {
    mode: "fixed_servers",
    rules: {
        singleProxy: {
            scheme: "%s",
            host: "%s",
            port: parseInt(%s)
        },
        bypassList: ["localhost"]
    },
};
chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});
chrome.webRequest.onAuthRequired.addListener(
    function (details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    },
    {urls: ["<all_urls>"]},
    ['blocking']
);
""" % (proxy['scheme'], proxy['host'], proxy['port'], proxy['username'], proxy['password'] )
        elif len(proxy) == 3:
            background_js = """
var config = {
        mode: "fixed_servers",
        rules: {
          singleProxy: {
            scheme: "%s",
            host: "%s",
            port: parseInt('%s')
          },
          bypassList: ["localhost"]
        },
      };

chrome.proxy.settings.set({value: config, scope: "regular"}, function() \{\});
""" % (proxy['scheme'], proxy['host'], proxy['port'])
        else:
            raise Exception('Could not create chrome extension, invalid proxy provided: %s'  % (str(proxy)))
        print(background_js.encode('utf8'))
        with ZipFile(pluginfile, 'w') as zp:
            zp.writestr("manifest.json", manifest_json.encode('utf8'))
            zp.writestr("background.js", background_js.encode('utf8'))
        return pluginfile
