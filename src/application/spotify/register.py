
from multiprocessing import current_process, Array, Process, sharedctypes, synchronize
from src.services.stats import Stats
from src.application.scenario import AbstractScenario
from xml.etree.ElementTree import VERSION
from src.services.httpserver import StatsProvider
from src.services.observer import Observer
from src.services.console import Console
from xvfbwrapper import Xvfb
from src.services.x11vncwrapper import X11vnc
from src.services.drivers import DriverManager
from src.application.spotify.Spotify import Adapter
from src.services.aws import RemoteQueue
from src.services.processes import ProcessManager, ProcessProvider
from random import randint
from shutil import rmtree
from gc import collect
from colorama import Fore
from src import VERSION
from src.services.users import UserManager
from src.services.proxies import PROXY_FILE_LISTENER, ProxyManager, PROXY_FILE_REGISTER
import os
from datetime import datetime
from src.services.config import Config
from psutil import cpu_count
import sys
from src.services.questions import Question

class RegisterStat:
    FILLING_OUT = 0
    SUBMITTING = 1
    CREATED = 2
    ERROR = 3
    DRIVER_NONE = 4

def runner(
    remoteQueue: RemoteQueue,
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    registerProxy: dict,
    playlist: str,
    vnc: bool,
    screenshotDir,
    stats: Array
):
        STATE_FILLING_OUT = 'filling_out'
        STATE_SUBMITTING = 'submitting'

        tid = current_process().pid
        console.log('#%d Start' % tid)

        driver = None
        userDataDir = None
        x11vnc = None
        vdisplay = None
        try:
            if shutdownEvent.is_set():
                return 
            vdisplay = None
            x11vnc = None
            if headless == False:
                width = 1280
                height = 1024
                if 'windowSize' in user:
                    [width,height] = user['windowSize'].split(',')
                vdisplay = Xvfb(width=width, height=height, colordepth=24, tempdir=None, noreset='+render')
                vdisplay.start()
                if vnc:
                    x11vnc = X11vnc(vdisplay)
                    x11vnc.start()

            driverManager = DriverManager(console, shutdownEvent)
            driverData = driverManager.getDriver(
                type='chrome',
                uid=tid,
                user=user,
                proxy=registerProxy,
                headless= headless
            )
            if not driverData:
                raise Exception('No driverData was returned from adapter')
            driver = driverData['driver']
            userDataDir = driverData['userDataDir']
            if not driver:
                raise Exception('No driver was returned from adapter')
            
        except:
            stats[RegisterStat.DRIVER_NONE] += 1
            console.exception('Driver unavailable')
        else:
            try:
                state = ''
                spotify = Adapter(driver, console, shutdownEvent)
                # __ COMPLETING __
                stats[RegisterStat.FILLING_OUT] += 1
                state = STATE_FILLING_OUT
                spotify.fillingOutSubscriptionForm(user)    
                stats[RegisterStat.FILLING_OUT] -= 1

                # __ SUBMITTING __
                stats[RegisterStat.SUBMITTING] += 1
                state = STATE_SUBMITTING
                spotify.submitSubscriptionForm()
                stats[RegisterStat.SUBMITTING] -= 1

                remoteQueue.sendMessage({
                    'user': user,
                    'playlist': playlist,
                    'type': 'sp'
                })
                stats[RegisterStat.CREATED] += 1
            except Exception as e:
                if state == STATE_FILLING_OUT:
                    stats[RegisterStat.FILLING_OUT] -= 1
                elif state == STATE_SUBMITTING:
                    stats[RegisterStat.SUBMITTING] -= 1
                stats[RegisterStat.ERROR] += 1
                try:
                    if screenshotDir:
                        id = randint(10000, 99999)
                        with open(screenshotDir + ('/%d.log' % id), 'w') as f:
                            f.write(str(e))
                        driver.save_screenshot(screenshotDir  + ('/%d.png' % id))
                except:
                    console.exception()
                            
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

class RegisterProcessProvider(ProcessProvider, Observer, StatsProvider):
    APP_SPOTIFY = 'sp'
    def __init__(self,
        basePath: str,
        accountCount: int,
        playlist: str,
        queueEndPoint: str,
        shutdownEvent: synchronize.Event,
        console: Console = None,
        headless: bool = False,
        vnc: bool = False,
        screenshotDir: str = None
        
    ):
        ProcessProvider.__init__(self)
        StatsProvider.__init__(self, 'runner')
        self.userManager = UserManager(basePath=basePath)
        self.registerProxyManager = ProxyManager(basePath=basePath, proxyFile=PROXY_FILE_REGISTER)
        self.listenerProxyManager = ProxyManager(basePath=basePath, proxyFile=PROXY_FILE_LISTENER)
        self.remoteQueue = RemoteQueue(endPoint=queueEndPoint)
        self.accountCount = accountCount
        self.playlist = playlist
        self.console = console
        self.headless = headless
        self.vnc = vnc
        self.screenshotDir = screenshotDir
        self.shutdownEvent = shutdownEvent
        self.registerStats = Array('i', [0, 0, 0, 0, 0])

    def getStats(self):
        return {
            'version': VERSION,
            'error': self.registerStats[RegisterStat.ERROR],
            'driverNone': self.registerStats[RegisterStat.DRIVER_NONE],
            'created': self.registerStats[RegisterStat.CREATED],
            'filling_out': self.registerStats[RegisterStat.FILLING_OUT],
            'submitting': self.registerStats[RegisterStat.SUBMITTING],
        }
    
    def getConsoleLines(self, width: int, height: int):
        stats = self.registerStats
        lines = []
        lines.append(Fore.WHITE + 'Created: %7d   Filling out form: %7d   Submitting: %7d   Error: %7d   Driver None: %7d' % 
            (stats[RegisterStat.CREATED],
            stats[RegisterStat.FILLING_OUT], 
            stats[RegisterStat.SUBMITTING],
            stats[RegisterStat.ERROR],
            stats[RegisterStat.DRIVER_NONE],
            ) 
        )
        return lines
        

    def notify(self, eventName: str, target, data):
        pass

    def getNewProcess(self, freeSlot: int):
        try:
            if self.registerStats[RegisterStat.CREATED] >= self.accountCount:
                return
            user = self.userManager.createRandomUser(
                proxy = self.listenerProxyManager.getRandomProxy(),
                application = RegisterProcessProvider.APP_SPOTIFY
            )

            p = Process(target = runner, kwargs={
                'remoteQueue': self.remoteQueue,
                'console': self.console, 
                'shutdownEvent': self.shutdownEvent, 
                'headless': True, #self.headless, 
                'vnc': self.vnc,
                'user': user,
                'registerProxy': self.registerProxyManager.getRandomProxy(),
                'playlist': self.playlist,
                'screenshotDir': self.screenshotDir,
                'stats': self.registerStats,
            })
            return p
        except Exception as e:
            self.console.exception()
            self.registerStats[RegisterStat.ERROR] += 1

class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def start(self):
        logDir = self.userDir + '/register/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
        screenshotDir = logDir + '/screenshot'
        
        if self.args.nolog == False:
            os.makedirs(logDir, exist_ok=True)
        if self.args.screenshot:
            os.makedirs(screenshotDir, exist_ok=True)
        
        
        
        #print('Configuration file: %s' % configFile)

        defautlConfig = {
            'sqs_endpoint': '',
            'max_process': cpu_count(),
            'spawn_interval': 0.5
        }
        
        registerConfig = Config.getRegisterConfig(self.configFile, defautlConfig)

        if not registerConfig:
            sys.exit('I can not continue without configuraton')
        

        #https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46
        
        if self.args.verbose:
            verbose = 3
        else:
            verbose = 1

        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logDir + '/session.log', logToFile=not self.args.nolog)

        if not registerConfig['sqs_endpoint']:
            sys.exit('you need to set the sqs_endpoint in the config file.')

        if not registerConfig['server_id']:
            sys.exit('you need to set the server_id in the config file.')

        questions = [
            {
                'type': 'input',
                'name': 'playlist',
                'message': 'Which playlist to listen ?',
                'validate': Question.validateUrl
            },
            {
                'type': 'input',
                'name': 'account_count',
                'message': 'How much account to create ?',
                'validate': Question.validateInteger,
                'filter': int
            },
            {
                'type': 'input',
                'name': 'max_process',
                'message': 'How much process to start ?',
                'default': str(registerConfig['max_process']),
                'validate': Question.validateInteger,
                'filter': int
            },
            {
            'type': 'confirm',
            'message': 'Ok, please type [enter] to start or [n] to abort',
            'name': 'continue',
            'default': True,
            },
        ]

        answers = Question.list(questions)
        
        if not 'continue' in answers or answers['continue'] == False:
            sys.exit('Ok, see you soon :-)')
        
        playlist = answers['playlist']
        accountCount = answers['account_count']
        maxProcess = answers['max_process']
        
        pp = RegisterProcessProvider(
            basePath=self.userDir,
            accountCount=accountCount,
            playlist=playlist,
            queueEndPoint=registerConfig['sqs_endpoint'],
            shutdownEvent=self.shutdownEvent,
            console= console,
            headless=self.args.headless,
            vnc= self.args.vnc,
            screenshotDir=screenshotDir
            )
        showInfo = not self.args.noinfo
        systemStats = Stats()
        pm = ProcessManager(
            serverId=registerConfig['server_id'],
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=maxProcess,
            spawnInterval=registerConfig['spawn_interval'],
            shutdownEvent=self.shutdownEvent,
            stopWhenNoProcess=True,
            showInfo=showInfo,
            systemStats=systemStats
        )
        devnull = open(os.devnull, "w") 
        sys.stderr = devnull 
        pm.start()