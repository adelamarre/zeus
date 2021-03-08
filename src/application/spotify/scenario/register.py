
import os
from re import A
from src.application.spotify.scenario.inputs.register import RegisterInputs
from src.application.spotify.scenario.config.register import RegisterConfig
from src.services.db import Db
import sys
from datetime import datetime
from gc import collect
from multiprocessing import (Array, Process, Queue, current_process, synchronize)
from random import randint
from shutil import rmtree
from time import sleep
from xml.etree.ElementTree import VERSION

from colorama import Fore
from psutil import cpu_count
from src import VERSION
from src.application.scenario import AbstractScenario
from src.application.spotify.Spotify import Adapter
from src.services.aws import RemoteQueue
from src.services.config import Config
from src.services.console import Console
from src.services.drivers import DriverManager
from src.services.httpserver import StatsProvider
from src.services.observer import Observer
from src.services.processes import ProcessManager, ProcessProvider
from src.services.proxies import (PROXY_FILE_LISTENER, PROXY_FILE_REGISTER,
                                  ProxyManager)
from src.services.questions import Question
from src.services.stats import Stats
from src.services.users import UserManager
from src.services.x11vncwrapper import X11vnc
from xvfbwrapper import Xvfb
from time import time,sleep
from src.application.spotify.stats import RegisterStat, RegisterRemoteStat

def runner(
    remoteQueue: RemoteQueue,
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    registerProxy: dict,
    playlist: str,
    playConfig: str,
    contractId: str,
    vnc: bool,
    screenshotDir,
    statsQueue: Queue
):
        STATE_FILLING_OUT = 'filling_out'
        STATE_SUBMITTING = 'submitting'
        STATE_STARTED = 'started'
        tid = current_process().pid
        driver = None
        userDataDir = None
        x11vnc = None
        vdisplay = None
        try:
            if shutdownEvent.is_set():
                return
            statsQueue.put((RegisterStat.PREPARE, 1))
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
            statsQueue.put((RegisterStat.PREPARE, -1))
            statsQueue.put((RegisterStat.DRIVER_NONE, 1))
            console.exception('Driver unavailable')
        else:
            try:
                statsQueue.put((RegisterStat.PREPARE, -1))
                state = STATE_STARTED
                spotify = Adapter(driver, console, shutdownEvent)
                # __ COMPLETING __
                statsQueue.put((RegisterStat.FILLING_OUT, 1))
                state = STATE_FILLING_OUT
                spotify.fillingOutSubscriptionForm(user)    
                statsQueue.put((RegisterStat.FILLING_OUT, -1))

                # __ SUBMITTING __
                statsQueue.put((RegisterStat.SUBMITTING, 1))
                state = STATE_SUBMITTING
                spotify.submitSubscriptionForm()
                statsQueue.put((RegisterStat.SUBMITTING, -1))

                remoteQueue.sendMessage({
                    'user': user,
                    'playlist': playlist,
                    'playConfig': playConfig,
                    'contractId': contractId,
                    'type': 'account'
                })

                statsQueue.put((RegisterStat.CREATED, 1))
            except Exception as e:
                if state == STATE_FILLING_OUT:
                    statsQueue.put((RegisterStat.FILLING_OUT, -1))
                elif state == STATE_SUBMITTING:
                    statsQueue.put((RegisterStat.SUBMITTING, -1))
                statsQueue.put((RegisterStat.ERROR, 1))
                console.exception()
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

def dryRunner(
    remoteQueue: RemoteQueue,
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    registerProxy: dict,
    playlist: str,
    playConfig: str,
    vnc: bool,
    screenshotDir,
    statsQueue: Queue
):
    STATE_FILLING_OUT = 'filling_out'
    STATE_SUBMITTING = 'submitting'
    STATE_STARTED = 'started'

    def sleepOrNot(secondes: int) -> bool:
        startSleep = time()
        while True:
            sleep(1)
            if randint(0,1000) > 999: 
                raise Exception('Dry exception')
            if shutdownEvent.is_set():
                return True
            if (time() - startSleep) > secondes:
                break
        return False

    tid = current_process().pid
    console.log('#%d Start' % tid)

    driver = None
    userDataDir = None
    x11vnc = None
    vdisplay = None
    
    try:
        state = STATE_STARTED
        spotify = Adapter(driver, console, shutdownEvent)
        # __ COMPLETING __
        statsQueue.put((RegisterStat.FILLING_OUT, 1))
        state = STATE_FILLING_OUT
        sleepOrNot(45)
        statsQueue.put((RegisterStat.FILLING_OUT, -1))

        # __ SUBMITTING __
        statsQueue.put((RegisterStat.SUBMITTING, 1))
        state = STATE_SUBMITTING
        sleepOrNot(randint(20, 40))
        statsQueue.put((RegisterStat.SUBMITTING, -1))
        statsQueue.put((RegisterStat.CREATED, 1))
    except Exception as e:
        if state == STATE_FILLING_OUT:
            statsQueue.put((RegisterStat.FILLING_OUT, -1))
        elif state == STATE_SUBMITTING:
            statsQueue.put((RegisterStat.SUBMITTING, -1))
        statsQueue.put((RegisterStat.ERROR, 1))
        try:
            if screenshotDir:
                id = randint(10000, 99999)
                with open(screenshotDir + ('/%d.log' % id), 'w') as f:
                    f.write(str(e))
                driver.save_screenshot(screenshotDir  + ('/%d.png' % id))
        except:
            console.exception()

class RegisterProcessProvider(ProcessProvider, Observer, StatsProvider):
    APP_SPOTIFY = 'sp'
    def __init__(self,
        appArgs,
        basePath: str,
        accountCount: int,
        playlist: str,
        playConfig: str,
        contractId: str,
        queueEndPoint: str,
        shutdownEvent: synchronize.Event,
        console: Console = None,
        headless: bool = False,
        vnc: bool = False,
        screenshotDir: str = None
    ):
        ProcessProvider.__init__(self, appArgs)
        StatsProvider.__init__(self, 'runner')
        self.userManager = UserManager(basePath=basePath)
        self.registerProxyManager = ProxyManager(basePath=basePath, proxyFile=PROXY_FILE_REGISTER)
        self.listenerProxyManager = ProxyManager(basePath=basePath, proxyFile=PROXY_FILE_LISTENER)
        self.remoteQueue = RemoteQueue(endPoint=queueEndPoint)
        self.accountCount = accountCount
        self.playlist = playlist
        self.playConfig = playConfig
        self.console = console
        self.headless = headless
        self.vnc = vnc
        self.screenshotDir = screenshotDir
        self.shutdownEvent = shutdownEvent
        self.registerStats = Array('i', [0, 0, 0, 0, 0, 0])
        self.statsQueue = Queue()
        self.contractId = contractId

    def getStats(self):
        return RegisterRemoteStat.parse(self.registerStats)
    
    def updateStats(self):
        while True:
            try:
                type, value = self.statsQueue.get_nowait()
                self.registerStats[type] += value
            except:
                break

    def getConsoleLines(self, width: int, height: int):
        try:
            stats = self.getStats()
            if stats[RegisterRemoteStat.CREATED] > 0:
                stats['errorPercent'] = (stats[RegisterRemoteStat.ERROR] / stats[RegisterRemoteStat.CREATED]) * 100
            else:
                stats['errorPercent'] = 0.0
            
            lines = []
            dry = Fore.YELLOW + '(dry) ' + Fore.RESET if self.args.dryrun else ''
            lines.append(Fore.WHITE + dry + 'Prepare:{prepare:4d}   Filling out form:{fillingOut:4d}   Submitting:{submitting:4d}   Created:{created:7d}   Error:{errorPercent:6.2f}   Driver None:{driverNone:7d}'.format(**stats))
            return lines
        except BaseException as e:
            self.console.exception()
            return [Fore.RED + str(e)]
        

    def notify(self, eventName: str, target, data):
        if eventName == ProcessManager.EVENT_TIC:
            self.updateStats()

    def buildProcess(self, target, user={}, playlist=''):
        return Process(target = target, kwargs={
                    'remoteQueue': self.remoteQueue,
                    'console': self.console, 
                    'shutdownEvent': self.shutdownEvent, 
                    'headless': True, #self.headless, 
                    'vnc': self.vnc,
                    'user': user,
                    'registerProxy': self.registerProxyManager.getRandomProxy(),
                    'playlist': playlist,
                    'screenshotDir': self.screenshotDir,
                    'statsQueue': self.statsQueue,
                    'playConfig': self.playConfig,
                    'contractId': self.contractId
                })

    def getNewProcess(self, freeSlot: int):
        try:
            if self.args.dryrun:
                if randint(0, 1000) == 34:
                    self.statsQueue.put((RegisterStat.ERROR, 1))
                    return
                return self.buildProcess(target=dryRunner)

            if self.registerStats[RegisterStat.CREATED] >= self.accountCount:
                return
            user = self.userManager.createRandomUser(
                proxy = self.listenerProxyManager.getRandomProxy(),
                application = RegisterProcessProvider.APP_SPOTIFY
            )
            p = self.buildProcess(target=runner, user=user, playlist=self.playlist)
            return p
        except Exception as e:
            self.console.exception()
            self.registerStats[RegisterStat.ERROR] += 1

class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def start(self):
        logDir = None
        screenshotDir = None
        logfile = None
        
        if self.args.nolog == False:
            logDir = self.userDir + '/register/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
            logfile = logDir + '/session.log'
            os.makedirs(logDir, exist_ok=True)
            if self.args.screenshot:
                screenshotDir = logDir + '/screenshot'
                os.makedirs(screenshotDir, exist_ok=True)
        
        #print('Configuration file: %s' % configFile)

        configData = RegisterConfig(self.userDir + '/config.ini').getConfig({
            'account_sqs_endpoint': '',
            'stats_sqs_endpoint': '',
            'max_process': cpu_count(),
            'spawn_interval': 0.5
        })
        
        verbose = 1
        if self.args.verbose:
            verbose = 3

        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        
        answers = RegisterInputs(console, self.shutdownEvent, configData, self.userDir).getInputs()
        
        if answers is None:
            sys.exit('Ok, see you soon :-)')
            
        print(answers)
        sys.exit()

        pp = RegisterProcessProvider(
            appArgs=self.args,
            basePath=self.userDir,
            accountCount=answers[RegisterInputs.ACCOUNT_COUNT],
            playlist=answers[RegisterInputs.PLAYLIST],
            playConfig=answers[RegisterInputs.PLAY_CONFIG],
            contractId=answers[RegisterInputs.CONTRACT_ID],
            queueEndPoint=configData[RegisterConfig.ACCOUNT_SQS_ENDPOINT],
            shutdownEvent=self.shutdownEvent,
            console= console,
            headless=self.args.headless,
            vnc= self.args.vnc,
            screenshotDir=screenshotDir
        )
        
        pm = ProcessManager(
            serverId=configData[RegisterConfig.SERVER_ID],
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=answers[RegisterInputs.MAX_PROCESS],
            spawnInterval=configData[RegisterConfig.SPAWN_INTERVAL],
            shutdownEvent=self.shutdownEvent,
            stopWhenNoProcess=True,
            showInfo=not self.args.noinfo,
            systemStats=Stats() if not self.sys.args.noinfo else None
        )
        devnull = open(os.devnull, "w") 
        sys.stderr = devnull
        pm.start()
        
