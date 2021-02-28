from multiprocessing import Event
import tty
from src.services.proxies import PROXY_FILE_REGISTER, ProxyManager, PROXY_FILE_LISTENER, Proxy
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
from src.services.drivers import DriverManager

import fcntl
import os
import selectors

if __name__ == '__main__':
    console = Console()
    runTest = True
    if runTest:
        pm = ProxyManager(PROXY_FILE_LISTENER)
        proxy = pm.getRandomProxy()
        dm = DriverManager(Console(), Event())
        vdisplay=Xvfb()
        vdisplay.start()
        x11vnc = X11vnc(vdisplay)
        x11vnc.start()
        driverData = dm.getDriver('chrome', 1, {}, proxy, False)
        driver = driverData['driver']
        
        spotify = Spotify.Adapter(driver, console, Event())
        ip = spotify.getMyIp()
        console.success('%s' % ip)

    #info = spotify.getClientInfo('http://ec2-35-180-119-212.eu-west-3.compute.amazonaws.com')
    #info = spotify.getClientInfo('http://35.180.119.212')
    #if 'server' in info:        
    #    console.success('Browser identity: %s, %s' % (info['server']['REMOTE_ADDR'], info['server']['HTTP_USER_AGENT']))
    #else:
    #    console.error('Check proxy error: getClientInfo return :\n%s' % info['raw'])

    
    while True:
        try:
            time.sleep(2)
            #if sys.stdin.buffer.readable:
            #console.clearScreen()
            #console.printAt(10, 10, 'Press q to quit')
            #if (console.getch() == 'q'):
            #    break
            

        except KeyboardInterrupt:
            break
        except:
            break

    if runTest:
        driver.quit()
        x11vnc.stop()
        vdisplay.stop()