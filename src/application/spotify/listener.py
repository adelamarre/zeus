import os, sys
from src.application.scenario import AbstractScenario
from multiprocessing import current_process, Array, Queue, Process, synchronize
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

class ListenerStat:
    LOGGING_IN = 0
    PLAYING = 1
    PLAYED = 2
    ERROR = 3
    DRIVER_NONE = 4

class ListenerRemoteStat:
    VERSION = 'version'
    LOGGING_IN = 'loggingIn'
    PLAYING = 'playing'
    PLAYED = 'played'
    ERROR = 'error'
    DRIVER_NONE = 'driverNone'

    def parse(stats: Array) -> dict:
        return {
            ListenerRemoteStat.VERSION: VERSION,
            ListenerRemoteStat.ERROR: stats[ListenerStat.ERROR],
            ListenerRemoteStat.DRIVER_NONE: stats[ListenerStat.DRIVER_NONE],
            ListenerRemoteStat.PLAYED: stats[ListenerStat.PLAYED],
            ListenerRemoteStat.LOGGING_IN: stats[ListenerStat.LOGGING_IN],
            ListenerRemoteStat.PLAYING: stats[ListenerStat.PLAYING],
        }

def runner(
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    proxy: dict,
    playlist: str,
    vnc: bool,
    screenshotDir,
    stats: Array,
    statsQueue: Queue()
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
                proxy=proxy,
                headless= headless
            )
            if not driverData:
                raise Exception('No driverData was returned from adapter')
            driver = driverData['driver']
            userDataDir = driverData['userDataDir']
            if not driver:
                raise Exception('No driver was returned from adapter')
            
        except:
            statsQueue.put((ListenerStat.DRIVER_NONE, +1))
            console.exception('Driver unavailable')
        else:
            try:
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
                spotify.playPlaylist(playlist, shutdownEvent, 80, 100)
                statsQueue.put((ListenerStat.PLAYING, -1))
                statsQueue.put((ListenerStat.PLAYED, +1))
            except BaseException as e:
                if state == STATE_PLAYING:
                    statsQueue.put((ListenerStat.PLAYING, -1))
                elif state == STATE_LOGGING_IN:
                    statsQueue.put((ListenerStat.LOGGING_IN, -1))
                statsQueue.put((ListenerStat.ERROR, +1))
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
    proxy: dict,
    playlist: str,
    vnc: bool,
    screenshotDir,
    stats: Array,
    statsQueue: Queue
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
        queueEndPoint: str,
        shutdownEvent: synchronize.Event,
        console: Console = None,
        headless: bool = False,
        vnc: bool = False,
        screenshotDir: str = None,
        overridePlaylist: str = False
    ):
        ProcessProvider.__init__(self, appArgs)
        StatsProvider.__init__(self, 'runner')
        self.remoteQueue = RemoteQueue(endPoint=queueEndPoint)
        self.console = console
        self.headless = headless
        self.vnc = vnc
        self.screenshotDir = screenshotDir
        self.shutdownEvent = shutdownEvent
        self.overridePlaylist = overridePlaylist
        self.listenerStats = Array('i', [0, 0, 0, 0, 0], lock=True)
        self.statsQueue = Queue()
        
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

    def buildProcess(self, target, user={}, playlist=''):
        return Process(target = target, kwargs={
                    'console': self.console, 
                    'shutdownEvent': self.shutdownEvent, 
                    'headless': self.headless, 
                    'vnc': self.vnc,
                    'user': user,
                    'proxy': None,
                    'playlist': playlist,
                    'screenshotDir': self.screenshotDir,
                    'stats': self.listenerStats,
                    'statsQueue': self.statsQueue
                })

    def getNewProcess(self, freeSlot: int):

        if self.args.dryrun:
            if randint(0, 1000) == 34:
                self.listenerStats[ListenerStat.ERROR] += 1
                return
            return self.buildProcess(target=dryRunner)

        try:
            self.remoteQueue.provision(freeSlot)
            message = self.remoteQueue.pop()
            
            if message:
                body = loads(message['Body'])
                
                if self.overridePlaylist:
                    body['playlist'] = self.overridePlaylist

                p = self.buildProcess(target=runner, user=body['user'], playlist=body['playlist'])
                
                self.remoteQueue.deleteMessage(message)
                
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
        
        #print('Configuration file: %s' % configFile)

        defautlConfig = {
            'sqs_endpoint': '',
            'secret': '',
            'max_process': cpu_count(),
            'spawn_interval': 0.5
        }
        
        listenerConfig = Config.getListenerConfig(self.configFile, defautlConfig)

        if not listenerConfig:
            sys.exit('I can not continue without configuraton')
        
        #https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46
        
        if self.args.verbose:
            verbose = 3
        else:
            verbose = 1

        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logfile, logToFile=not self.args.nolog)

        if not listenerConfig['sqs_endpoint']:
            sys.exit('you need to set the sqs_endpoint in the config file.')

        if not listenerConfig['server_id']:
            sys.exit('you need to set the server_id in the config file.')

        if not listenerConfig['secret']:
            sys.exit('You need to provide the server stats password')


        questions = [
            {
                'type': 'input',
                'name': 'max_process',
                'message': 'How much process to start ?',
                'default': str(listenerConfig['max_process']),
                'validate': Question.validateInteger,
                'filter': int
            },
            {
                'type': 'confirm',
                'name': 'override_playlist',
                'message': 'Would you override the playlist to listen ?',
                'default': False
            },
            {
                'type': 'input',
                'name': 'playlist',
                'message': 'Playlist url ?',
                'default': '',
                'validate': Question.validateUrl,
                'when': Question.when('override_playlist')
            },
            {
                'type': 'confirm',
                'name': 'stats_server',
                'message': 'Would you start the statistics web server ?',
                'default': True
            },
            {
            'type': 'confirm',
            'message': 'Ok, please type [enter] to start or [n] to abort',
            'name': 'continue',
            'default': True,
            },
        ]
        answers = Question.list(questions)
        if not answers or not 'continue' in answers or answers['continue'] == False:
            sys.exit('ok, see you soon.')
        
        playlist = answers.get('playlist', None)
        maxProcess = answers['max_process']
        
        pp = ListenerProcessProvider(
            appArgs=self.args,
            queueEndPoint=listenerConfig['sqs_endpoint'],
            shutdownEvent=self.shutdownEvent,
            console= console,
            headless=self.args.headless,
            vnc= self.args.vnc,
            screenshotDir=screenshotDir,
            overridePlaylist=playlist,
            )

        
        showInfo = not self.args.noinfo
        systemStats = Stats()

        pm = ProcessManager(
            serverId=listenerConfig['server_id'],
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=maxProcess,
            spawnInterval=listenerConfig['spawn_interval'],
            showInfo=showInfo,
            shutdownEvent=self.shutdownEvent,
            systemStats= systemStats,
            stopWhenNoProcess=False
        )
        if answers['stats_server']:
            
            statsServer = HttpStatsServer(listenerConfig['secret'], console, self.userDir, [systemStats, pp, pm])
            statsServer.start()

        if self.args.dryrun:
            while not self.shutdownEvent.is_set():
               sleep(1)
        else:
            pm.start()

        if answers['stats_server']:
            statsServer.stop()