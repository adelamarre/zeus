
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
from src.services.proxies import PROXY_FILE_LISTENER, ProxyManager, PROXY_FILE_REGISTER
from src.services.x11vncwrapper import X11vnc
from json import dumps
from src.services.users import UserManager
from src.services.userAgents import UserAgentManager

class RegisterContext:
    def __init__(self, 
        accountsCount: Array, 
        threadsCount: Array, 
        channel: int, 
        config: Config, 
        maxThread: int, 
        lock: Lock, 
        shutdownEvent: Event, 
        console: Console,
        accountToCreate: int,
        playlist: str,
        vnc: bool = False
    ):
        self.maxThread = maxThread
        self.lock = lock
        self.shutdownEvent = shutdownEvent
        self.console = console
        self.config = config
        self.channel = channel
        self.threadsCount = threadsCount
        self.accountsCount = accountsCount
        self.accountToCreate = accountToCreate
        self.playlist = playlist
        self.vnc = vnc

class TaskContext:
    def __init__(self, user: dict, playlist: str, proxy: dict = None, vnc: bool = False):
        self.user = user
        self.playlist = playlist
        self.proxy = proxy
        self.vnc = vnc
        

class Register(Process):
    def __init__(self, pcontext: RegisterContext):
        super().__init__()
        self.p_context = pcontext
        self.driverManager = DriverManager(pcontext.console, startService=False)
        self.client = client('sqs')
        self.totalAccountCreated = 0
        self.proxyRegisterManager = ProxyManager(proxyFile=PROXY_FILE_REGISTER)
        self.proxyListenerManager = ProxyManager(proxyFile=PROXY_FILE_LISTENER)
        self.userManager = UserManager(self.p_context.console)
        self.userAgentManager = UserAgentManager()
        self.lockClient = Lock()
        self.lockDriver = Lock()
        self.lockAccountCount = Lock()

    def run(self):
        threads = []
        messages = []
        for x in range(self.p_context.accountToCreate):
            messages.append({
                    'Body': dumps({
                        'user': self.userManager.createRandomUser(
                            proxy = self.proxyListenerManager.getRandomProxy(),
                            userAgent= self.userAgentManager.getRandomUserAgent(),
                            application='spotify',
                        ),
                        'playlist': self.p_context.playlist
                    })
                }
            )
        while not self.p_context.shutdownEvent.is_set():
            try:
                sleep(self.p_context.config.LISTENER_SPAWN_INTERVAL)
                freeSlot = self.p_context.maxThread - len(threads) 
                
                if freeSlot and len(messages):
                    message = messages.pop()
                    body = loads(message['Body'])
                    t_context = TaskContext(
                        playlist=body['playlist'],
                        proxy=self.proxyRegisterManager.getRandomProxy(),
                        user=body['user'],
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
            except:
                self.p_context.console.exception('Register process #%d exception' % self.p_context.channel)
        
        self.driverManager.purge()
        del self.driverManager
        del self.p_context
        del self.userAgentManager
        del self.userManager
        del self.proxyListenerManager
        del self.proxyRegisterManager
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
            spotify = Spotify.Adapter(driver, self.p_context.console, self.p_context.shutdownEvent)
            self.p_context.console.log('#%d Start create account for %s' % (tid, t_context.user['email']))
            if spotify.register(t_context.user):
                self.p_context.console.log('#%d Account created for %s' % (tid, t_context.user['email']))
                message = {
                    'user': t_context.user,
                    'playlist': t_context.playlist
                }
                with self.lockClient:
                    try:
                        self.client.send_message(
                            QueueUrl=self.p_context.config.SQS_ENDPOINT,
                            MessageBody=dumps(message),
                            DelaySeconds=1,
                        )
                    except:
                        self.p_context.console.exception('T#%d Failed to send message to the queue %s' % (tid, self.p_context.config.SQS_ENDPOINT))
                    else:
                        self.p_context.console.log('#%d Message sent for %s' % (tid, t_context.user['email']))
                        with self.lockAccountCount:
                            self.totalAccountCreated += 1
                            self.p_context.accountsCount[self.p_context.channel] = self.totalAccountCreated
            else:
                self.p_context.console.error('#%d Failed to create account for %s' % (tid, t_context.user['email']))  

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