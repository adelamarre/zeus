
from gc import collect
from random import randint
from shutil import rmtree
from multiprocessing import Array, Lock, Process, Event
from threading import Thread, current_thread
from traceback import format_exc
from src.services.config import Config
from src.application.spotify import Spotify
from xvfbwrapper import Xvfb
from boto3 import client
from src.services.drivers import DriverManager
from src.services.console import Console
from time import sleep
from json import loads
from src.services.proxies import ProxyManager, PROXY_FILE_LISTENER
from src.services.x11vncwrapper import X11vnc

class ListenerContext:
    def __init__(self, console: Console, batchId: int,  user: dict, playlist: str, shutdownEvent: Event, proxy: dict = None, vnc: bool = False, headless = True):
        self.console = console
        self.batchId = batchId
        self.user = user
        self.playlist = playlist
        self.proxy = proxy
        self.vnc = vnc
        self.headless = headless
        self.shutdownEvent = shutdownEvent      
    
class Listener(Process):
    def __init__(self, pcontext: ListenerContext):
        Process.__init__(self)
        self.p_context = pcontext
        self.driverManager = DriverManager(pcontext.console, pcontext.shutdownEvent, startService=False)
        self.client = client('sqs')
        self.totalMessageReceived = 0
        self.proxyManager = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
        self.lockClient = Lock()
        self.lockDriver = Lock()

    def run(self):
        tid = current_thread().native_id
        self.p_context.console.log('#%d Start' % tid)
        driver = None
        try:
            if self.p_context.shutdownEvent.is_set():
                return 
            vdisplay = None
            x11vnc = None
            if t_context.headless == False:
                width = 1280
                height = 1024
                if 'windowSize' in t_context.user:
                    [width,height] = t_context.user['windowSize'].split(',')
                vdisplay = Xvfb(width=width, height=height, colordepth=24, tempdir=None, noreset='+render')
                vdisplay.start()
                if t_context.vnc:
                    x11vnc = X11vnc(vdisplay)
                    x11vnc.start()

            with self.lockDriver:
                driverData = self.driverManager.getDriver(
                    type='chrome',
                    uid=tid,
                    user=t_context.user,
                    proxy=t_context.proxy,
                    headless= t_context.headless
                )
            if not driverData:
                return
            driver = driverData['driver']
            userDataDir = driverData['userDataDir']
            if not driver:
                return
            
        except:
            self.p_context.console.error('Unavailale webdriver: %s' % format_exc())
        else:
            try:
                spotify = Spotify.Adapter(driver, self.p_context.console, self.p_context.shutdownEvent)
                if spotify.login(t_context.user['email'], t_context.user['password']):
                    self.p_context.console.log('#%d Logged In' % tid)
                    if not self.p_context.shutdownEvent.is_set():
                        self.p_context.console.log('#%d Start listening...' % tid)
                        spotify.playPlaylist(t_context.playlist, self.p_context.shutdownEvent, 90, 110)
                        self.p_context.console.log('#%d Played' % tid)
                with self.lockClient:
                    self.client.delete_message(
                        QueueUrl=self.p_context.config.SQS_ENDPOINT,
                        ReceiptHandle=t_context.receiptHandle
                    )
                    self.p_context.console.log('#%d Message deleted' % tid)
            except:
                self.p_context.console.exception()
                spotify.saveScreenshot()
                        
        if driver:
            try:
                driver.quit()
                del driver
            except:
                pass
        if userDataDir:
            try:
                rmtree(path=userDataDir, ignore_errors=True)
            except:
                pass
        if x11vnc: #Terminate vnc server if any
            try:
                x11vnc.stop()
                del x11vnc
            except:
                pass
        if vdisplay:
            try:
                vdisplay.stop()
                del vdisplay
            except:
                pass
        collect()