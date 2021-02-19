from multiprocessing import Event
from src.services.proxies import ProxyManager, PROXY_FILE_LISTENER, Proxy
from src.services.proxyplugin.auth import ProxyRedirect
from selenium.webdriver.chrome.options import Options
from seleniumwire import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from tempfile import mkdtemp
from src.application.spotify import Spotify
from src.services.console import Console
import proxy
import time
from xvfbwrapper import Xvfb
from src.services.x11vncwrapper import X11vnc

if __name__ == '__main__':
    pm = ProxyManager(PROXY_FILE_LISTENER)
    #Start proxy server

    #p = proxy.Proxy([], plugins=[ProxyRedirect])
   
    pm = ProxyManager()
    proxy = pm.getRandomProxy()
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
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    userDataDir = mkdtemp()
    options.add_argument('--user-data-dir=%s' % userDataDir)
    options.add_argument('--proxy-server=localhost:8899')
    options.add_argument("--headless")

    proxyStr = Proxy.getUrl(proxy)
    soptions = {
        'proxy': {
            'https': '%s' % proxyStr,
            'http': '%s' % proxyStr,
            'no_proxy': 'localhost,127.0.0.1',
        }
    }

    desired_capabilities = DesiredCapabilities.CHROME.copy()



    vdisplay = Xvfb(width=1280, height=1024, colordepth=24, tempdir=None, noreset='+render')
    vdisplay.start()
    x11vnc = X11vnc(vdisplay)
    x11vnc.start()

    driver = webdriver.Chrome(options=options, desired_capabilities=desired_capabilities, seleniumwire_options=soptions)
    
    
    #def requestInterceptor(request):
    #    try:
    #        request.headers['Zeus-proxy'] = '%s:%s:%s:%s' % (proxy['host'], proxy['port'], proxy['username'], proxy['password'])
    #    except:
    #        console.exception()

    #driver.request_interceptor = requestInterceptor



    console = Console()
    
    spotify = Spotify.Adapter(driver, console, Event())

    #info = spotify.getClientInfo('http://ec2-35-180-119-212.eu-west-3.compute.amazonaws.com')
    #info = spotify.getClientInfo('http://35.180.119.212')
    #if 'server' in info:        
    #    console.success('Browser identity: %s, %s' % (info['server']['REMOTE_ADDR'], info['server']['HTTP_USER_AGENT']))
    #else:
    #    console.error('Check proxy error: getClientInfo return :\n%s' % info['raw'])

    ip = spotify.getMyIp()
    console.success('My ip is : %s' % ip)

    while True:
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            break
        except:
            break

    driver.quit()
    x11vnc.stop()
    vdisplay.stop()