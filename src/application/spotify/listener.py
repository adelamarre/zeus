
from gc import collect
from shutil import rmtree
from multiprocessing import Lock, Process, Event
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

class ListenerContext:
    def __init__(self, config: Config, maxThread: int, lock: Lock, shutdownEvent: Event, console: Console):
        self.maxThread = maxThread
        self.lock = lock
        self.shutdownEvent = shutdownEvent
        self.console = console
        self.config = config

class TaskContext:
    def __init__(self, user: dict, playlist: str, receiptHandle: str, proxy: dict = None):
        self.user = user
        self.playlist = playlist
        self.proxy = proxy
        self.receiptHandle = receiptHandle
        

class Listener(Process):
    def __init__(self, pcontext: ListenerContext):
        super(self)
        self.p_context = pcontext
        self.driverManager = DriverManager(pcontext.console)
        self.client = client('sqs')
        self.totalMessageReceived = 0
        self.proxyManager = ProxyManager(proxyFile=PROXY_FILE_LISTENER)

    def run(self):
        threads = []
        messages = []

        while not self.p_context.shutdownEvent.is_set():
            sleep(self.p_context.config.LISTENER_SPAWN_INTERVAL)
            freeSlot = len(threads) - self.p_context.maxThread
            if len(messages) < 1:
                response = client.receive_message(
                    QueueUrl=self.p_context.config.SQS_URL,
                    MaxNumberOfMessages=freeSlot,
                    VisibilityTimeout=600,
                    WaitTimeSeconds=2,
                )
                if 'Messages' in response:
                    newMessages = response['Messages']
                    messages =  newMessages + messages
                    self.totalMessageReceived += len(messages)

            
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
                    receiptHandle=message['ReceiptHandle']
                )
                t = Thread(target=self.runner, args=(t_context,))
                threads.append(t)
                t.start()
            
            leftThread = []
            for thread in threads:
                if thread.is_alive():
                    leftThread.append(thread)
                else:
                    del thread
                    collect()
            threads = leftThread
            if len(threads) == 0:
                break
        
        del self.driverManager
        del self.p_context
        collect()


    def runner(self, t_context: TaskContext):
        tid = current_thread().native_id
        try: 
            vdisplay = Xvfb(width=1280, height=1024, colordepth=24, tempdir=None, noreset='+render')
            vdisplay.start()
            driverData = self.driverManager.getDriver(
                type='chrome',
                uid=tid,
                user=t_context.user,
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
            spotify = Spotify.Adapter(driver, self.p_context.console, self.p_context.shutdownEvent)
            if spotify.login(t_context.user['email'], t_context.user['password']):
                if not self.p_context.shutdownEvent.is_set():
                    spotify.playPlaylist(t_context.playlist, self.p_context.shutdownEvent, 90, 110)
            
            self.client.delete_message(
                QueueUrl=self.p_context.config.SQS_URL,
                ReceiptHandle=t_context.receiptHandle
            )
                       
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
        if vdisplay:
            try:
                vdisplay.stop()
                del vdisplay
            except:
                pass
        collect()