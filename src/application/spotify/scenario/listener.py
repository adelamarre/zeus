import os, sys
from src.application.spotify.scenario.inputs.listener import ListenerInputs
from src.application.spotify.scenario.config.listener import ListenerConfig
from typing import List
from src.application.spotify.parser.playlist import TrackList, Track
from src.application.statscollector import StatsCollector
from src.application.scenario import AbstractScenario
from multiprocessing import current_process, Array, Queue, Process, synchronize
from src.services.httpserver import StatsProvider
from src.services.observer import Observer
from src.services.console import Console
from xvfbwrapper import Xvfb
from src.services.x11vncwrapper import X11vnc
from src.services.drivers import DriverManager
from src.application.spotify.Spotify import Adapter
from src.services.aws import RemoteQueue
from src.services.processes import ProcessManager, ProcessProvider
from src.services.questions import Question
from src.services.config import Config
from random import randint
from shutil import rmtree
from gc import collect
from json import loads
from datetime import datetime
from colorama import Fore
from src import VERSION
from psutil import cpu_count
from src.services.httpserver import HttpStatsServer
from src.services.stats import Stats
from time import sleep, time
from src.application.spotify.stats import ListenerRemoteStat, ListenerStat

def runner(
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    playlistUrl: str,
    playConfig: str,
    vnc: bool,
    screenshotDir,
    statsQueue: Queue,
    statsCollector: StatsCollector,
    contractId: str
    ):
        STATE_LOGGING_IN = 'logging_in'
        STATE_PLAYING = 'playing'
        STATE_STARTED = 'started'
        tid = current_process().pid
        console.log('#%d Start' % tid)

        driver = None
        userDataDir = None
        x11vnc = None
        vdisplay = None
        try:
            if shutdownEvent.is_set():
                return 
            statsQueue.put((ListenerStat.PREPARE, +1))
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
                headless= headless
            )
            if not driverData:
                raise Exception('No driverData was returned from adapter')
            driver = driverData['driver']
            userDataDir = driverData['userDataDir']
            if not driver:
                raise Exception('No driver was returned from adapter')
            
        except:
            statsQueue.put((ListenerStat.PREPARE, -1))
            statsQueue.put((ListenerStat.DRIVER_NONE, +1))
            console.exception('Driver unavailable')
        else:
            try:
                statsQueue.put((ListenerStat.PREPARE, -1))
                state = STATE_STARTED
                spotify = Adapter(driver, console, shutdownEvent)
                # __ LOGGING __
                statsQueue.put((ListenerStat.LOGGING_IN, +1))
                state = STATE_LOGGING_IN
                spotify.login(user['email'], user['password'])    
                statsQueue.put((ListenerStat.LOGGING_IN, -1))
            
                # __ PLAYING __
                statsQueue.put((ListenerStat.PLAYING, +1))
                state = STATE_PLAYING
                
                spotify.play(
                    user=user,
                    playlistUrl=playlistUrl,
                    playConfig=playConfig,
                    statsCollector=statsCollector,
                    statsQueue=statsQueue,
                    contractId=contractId
                )

                statsQueue.put((ListenerStat.PLAYING, -1))

            except BaseException as e:
                if state == STATE_PLAYING:
                    statsQueue.put((ListenerStat.PLAYING, -1))
                elif state == STATE_LOGGING_IN:
                    statsQueue.put((ListenerStat.LOGGING_IN, -1))
                statsQueue.put((ListenerStat.ERROR, +1))
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
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    playlistUrl: str,
    vnc: bool,
    screenshotDir,
    statsQueue: Queue,
    statsCollector: StatsCollector,
    playConfig: str
    ):
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

        STATE_LOGGING_IN = 'logging_in'
        STATE_PLAYING = 'playing'
        STATE_STARTED = 'started'
        #getDriver
        #sleep(5)
        try:
            state = STATE_STARTED
            # __ LOGGING __
            statsQueue.put((ListenerStat.LOGGING_IN, +1))
            state = STATE_LOGGING_IN
            sleepOrNot(10)
            statsQueue.put((ListenerStat.LOGGING_IN, -1))
            # __ PLAYING __
            statsQueue.put((ListenerStat.PLAYING, +1))
            state = STATE_PLAYING
            sleepOrNot(randint(20, 25))
            statsQueue.put((ListenerStat.PLAYING, -1))
            statsQueue.put((ListenerStat.PLAYED, +1))
        except BaseException as e:
            print(str(e))
            if state == STATE_PLAYING:
                statsQueue.put((ListenerStat.PLAYING, -1))
            elif state == STATE_LOGGING_IN:
                statsQueue.put((ListenerStat.LOGGING_IN, -1))
            statsQueue.put((ListenerStat.ERROR, +1))

class ListenerProcessProvider(ProcessProvider, Observer, StatsProvider):
    def __init__(self,
        appArgs,
        accountRemoteQueue: RemoteQueue,
        shutdownEvent: synchronize.Event,
        statsCollector: StatsCollector = None,
        console: Console = None,
        headless: bool = False,
        vnc: bool = False,
        screenshotDir: str = None,
        overridePlaylist: str = False,
        overridePlayConfig: str = False
    ):
        ProcessProvider.__init__(self, appArgs)
        StatsProvider.__init__(self, 'runner')
        self.accountRemoteQueue = accountRemoteQueue
        self.statsCollector = statsCollector
        self.console = console
        self.headless = headless
        self.vnc = vnc
        self.screenshotDir = screenshotDir
        self.shutdownEvent = shutdownEvent
        self.overridePlaylist = overridePlaylist
        self.listenerStats = Array('i', [0, 0, 0, 0, 0, 0], lock=True)
        self.statsQueue = Queue()
        self.overridePlayConfig = overridePlayConfig
        
    def getStats(self) -> dict:
        return ListenerRemoteStat.parse(self.listenerStats)

    def updateStats(self):
        while True:
            try:
                type, value = self.statsQueue.get_nowait()
                self.listenerStats[type] += value
            except:
                break

    def getConsoleLines(self, width: int, height: int):
        stats = self.getStats()
        lines = []
        if stats[ListenerRemoteStat.PLAYED] > 0:
            stats['errorPercent'] = (stats[ListenerRemoteStat.ERROR] / stats[ListenerRemoteStat.PLAYED]) * 100
        else:
            stats['errorPercent'] = 0.0
        
        dry = dry = Fore.YELLOW + '(dry) ' + Fore.RESET  if self.args.dryrun else ''
        lines.append(Fore.WHITE + dry + 'Logging in: {loggingIn:7d}   Playing: {playing:7d}   Played: {played:7d}   Error: {errorPercent:6.2f}%   Driver None: {driverNone:7d}'.format(**stats))
        return lines
        
    def notify(self, eventName: str, target, data):
        if eventName == ProcessManager.EVENT_TIC:
            self.updateStats()

    def buildProcess(self, target, contractId:str, user={}, playlist='', playConfig='1:1'):
        return Process(target = target, kwargs={
                    'console': self.console, 
                    'shutdownEvent': self.shutdownEvent, 
                    'headless': self.headless, 
                    'vnc': self.vnc,
                    'user': user,
                    'playlistUrl': playlist,
                    'playConfig': playConfig,
                    'screenshotDir': self.screenshotDir,
                    'statsQueue': self.statsQueue,
                    'statsCollector': self.statsCollector,
                    'contractId': contractId
                })

    def getNewProcess(self, freeSlot: int):

        if self.args.dryrun:
            if randint(0, 1000) == 34:
                self.listenerStats[ListenerStat.ERROR] += 1
                return
            return self.buildProcess(target=dryRunner)

        try:
            self.accountRemoteQueue.provision(freeSlot)
            message = self.accountRemoteQueue.pop()
            
            if message:
                body = loads(message['Body'])
                
                if self.overridePlaylist:
                    body['playlist'] = self.overridePlaylist
                if self.overridePlayConfig:
                    body['playConfig'] = self.overridePlayConfig
                
                contractId = body.get('contractId', 'undefined')
                playConfig = body.get('playConfig', '1:1')
                
                p = self.buildProcess(target=runner, user=body['user'], contractId=contractId, playlist=body['playlist'], playConfig=playConfig)
                self.accountRemoteQueue.deleteMessage(message)
                
                return p
        except Exception as e:
            self.console.exception()
            self.listenerStats[ListenerStat.ERROR] += 1

class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.configFile = self.userDir + '/config.ini' 

    def start(self):
        logDir = None
        screenshotDir = None
        logfile = None
        
        if self.args.nolog == False:
            logDir = self.userDir + '/listener/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
            logfile = logDir + '/session.log'
            os.makedirs(logDir, exist_ok=True)
            if self.args.screenshot:
                screenshotDir = logDir + '/screenshot'
                os.makedirs(screenshotDir, exist_ok=True)

        verbose = 3 if self.args.verbose else 1
        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)
        console.log('Start scenario Spotify listener')

        config = ListenerConfig(self.configFile)
        configData = config.getConfig({
            'account_sqs_endpoint': '',
            'collector_sqs_endpoint': '',
            'secret': '',
            'max_process': cpu_count(),
            'spawn_interval': 0.5
        })
        

        

        answers = ListenerInputs(console, self.shutdownEvent, configData, self.userDir).getInputs()
        if answers is None:
            sys.exit('ok, see you soon.')
        
        proivideStatsServer = answers[ListenerInputs.STATS_SERVER]
        playlist            = answers[ListenerInputs.PLAYLIST]
        maxProcess          = answers[ListenerInputs.MAX_PROCESS]
        accountRemoteQueue  = RemoteQueue(configData[ListenerConfig.ACCOUNT_SQS_ENDPOINT])
        statCollector       = StatsCollector(configData[ListenerConfig.COLLECTOR_SQS_ENDPOINT], 'spotify', configData[ListenerConfig.SERVER_ID])
        
        pp = ListenerProcessProvider(
            appArgs=self.args,
            accountRemoteQueue=accountRemoteQueue,
            statsCollector=statCollector,
            shutdownEvent=self.shutdownEvent,
            console= console,
            headless=self.args.headless,
            vnc= self.args.vnc,
            screenshotDir=screenshotDir,
            overridePlaylist=playlist,
        )

        systemStats = Stats()

        pm = ProcessManager(
            serverId=configData[ListenerConfig.SERVER_ID],
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=maxProcess,
            spawnInterval=configData[ListenerConfig.SPAWN_INTERVAL],
            showInfo=not self.args.noinfo,
            shutdownEvent=self.shutdownEvent,
            systemStats= systemStats,
            stopWhenNoProcess=False
        )

        if proivideStatsServer:
            statsServer = HttpStatsServer(configData[ListenerConfig.SECRET], console, self.userDir, [systemStats, pp, pm])
            statsServer.start()

        if self.args.dryrun:
            while not self.shutdownEvent.is_set():
               sleep(1)
        else:
            pm.start()

        if proivideStatsServer:
            statsServer.stop()