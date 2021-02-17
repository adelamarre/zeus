
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
    def __init__(self, 
        messagesCount: Array, 
        threadsCount: Array, 
        channel: int, 
        config: Config, 
        maxThread: int, 
        lock: Lock, 
        shutdownEvent: Event, 
        console: Console,
        vnc: bool = False
    ):
        self.maxThread = maxThread
        self.lock = lock
        self.shutdownEvent = shutdownEvent
        self.console = console
        self.config = config
        self.channel = channel
        self.threadsCount = threadsCount
        self.messagesCount = messagesCount
        self.vnc = vnc

class TaskContext:
    def __init__(self, user: dict, playlist: str, receiptHandle: str, proxy: dict = None, vnc: bool = False):
        self.user = user
        self.playlist = playlist
        self.proxy = proxy
        self.receiptHandle = receiptHandle
        self.vnc = vnc
        

class Listener(Process):
    def __init__(self, pcontext: ListenerContext):
        super().__init__()
        self.p_context = pcontext
        self.driverManager = DriverManager(pcontext.console, startService=False)
        self.client = client('sqs')
        self.totalMessageReceived = 0
        self.proxyManager = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
        self.lockClient = Lock()
        self.lockDriver = Lock()

    def run(self):
        threads = []
        messages = []

        while not self.p_context.shutdownEvent.is_set():
            sleep(self.p_context.config.LISTENER_SPAWN_INTERVAL)
            freeSlot = self.p_context.maxThread - len(threads) 
            if len(messages) < 1 and freeSlot:
                try:
                    with self.lockClient:
                        response = self.client.receive_message(
                            QueueUrl=self.p_context.config.SQS_ENDPOINT,
                            MaxNumberOfMessages=freeSlot,
                            VisibilityTimeout=600,
                            WaitTimeSeconds=2,
                        )
                    if 'Messages' in response:
                        newMessages = response['Messages']
                        messages =  newMessages + messages
                        self.totalMessageReceived += len(newMessages)
                        self.p_context.messagesCount[self.p_context.channel] = self.totalMessageReceived
                except:
                    self.p_context.console.exception()
            if freeSlot and len(messages):
                message = messages.pop()
                body = loads(message['Body'])
                proxy = None
                if self.p_context.config.LISTENER_OVERIDE_PLAYLIST:
                    body['playlist'] = self.p_context.config.LISTENER_OVERIDE_PLAYLIST
                if self.p_context.config.LISTENER_OVERIDE_PROXY:
                    proxy = self.proxyManager.getRandomProxy()
                
                t_context = TaskContext(
                    playlist=body['playlist'],
                    proxy=proxy,
                    user=body['user'],
                    receiptHandle=message['ReceiptHandle'],
                    vnc = self.p_context.vnc
                )
                t = Thread(target=self.runner, args=(t_context,))
                t.start()
                threads.append(t)

            leftThread = []
            for thread in threads:
                if thread.is_alive():
                    leftThread.append(thread)
                else:
                    del thread
                    collect()
            threads = leftThread
            self.p_context.threadsCount[self.p_context.channel] = len(threads)
            if len(threads) == 0:
                break
        
        del self.driverManager
        del self.p_context
        collect()


    def runner(self, t_context: TaskContext):
        tid = current_thread().native_id
        self.p_context.console.log('#%d Start' % tid)
        try:
            if self.p_context.shutdownEvent.is_set():
                return 
            vdisplay = None
            x11vnc = None
            if t_context.vnc:
                vdisplay = Xvfb(width=1280, height=1024, colordepth=24, tempdir=None, noreset='+render')
                vdisplay.start()
                x11vnc = X11vnc(vdisplay)
                x11vnc.start()

            with self.lockDriver:
                driverData = self.driverManager.getDriver(
                    type='chrome',
                    uid=tid,
                    user=t_context.user,
                    proxy=t_context.proxy,
                    headless= not t_context.vnc
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