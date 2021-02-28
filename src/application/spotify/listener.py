
import os, sys
from src.application.scenario import AbstractScenario
from multiprocessing import current_process, Array, Process, sharedctypes, synchronize
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



class ListenerStat:
    LOGGING_IN = 0
    PLAYING = 1
    PLAYED = 2
    ERROR = 3
    DRIVER_NONE = 4

def runner(
    console: Console, 
    shutdownEvent: synchronize.Event, 
    headless: bool, 
    user: dict,
    proxy: dict,
    playlist: str,
    vnc: bool,
    screenshotDir,
    stats: Array
    ):
        STATE_LOGGING_IN = 'logging_in'
        STATE_PLAYING = 'playing'

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
            stats[ListenerStat.DRIVER_NONE] += 1
            console.exception('Driver unavailable')
        else:
            try:
                state = ''
                spotify = Adapter(driver, console, shutdownEvent)
                # __ LOGGING __
                stats[ListenerStat.LOGGING_IN] += 1
                state = STATE_LOGGING_IN
                spotify.login(user['email'], user['password'])    
                stats[ListenerStat.LOGGING_IN] -= 1

                # __ PLAYING __
                stats[ListenerStat.PLAYING] += 1
                state = STATE_PLAYING
                spotify.playPlaylist(playlist, shutdownEvent, 80, 100)
                stats[ListenerStat.PLAYING] -= 1
                stats[ListenerStat.PLAYED] += 1
            except Exception as e:
                if state == STATE_PLAYING:
                    stats[ListenerStat.PLAYING] -= 1
                elif state == STATE_LOGGING_IN:
                    stats[ListenerStat.LOGGING_IN] -= 1
                stats[ListenerStat.ERROR] += 1
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

class ListenerProcessProvider(ProcessProvider, Observer, StatsProvider):
    def __init__(self,
        queueEndPoint: str,
        shutdownEvent: synchronize.Event,
        console: Console = None,
        headless: bool = False,
        vnc: bool = False,
        screenshotDir: str = None,
        overridePlaylist: str = False
    ):
        ProcessProvider.__init__(self)
        StatsProvider.__init__(self, 'runner')
        self.remoteQueue = RemoteQueue(endPoint=queueEndPoint)
        self.console = console
        self.headless = headless
        self.vnc = vnc
        self.screenshotDir = screenshotDir
        self.shutdownEvent = shutdownEvent
        self.overridePlaylist = overridePlaylist
        self.listenerStats = Array('i', 5)
        self.listenerStats[ListenerStat.PLAYED] = 0
        self.listenerStats[ListenerStat.ERROR] = 0
        self.listenerStats[ListenerStat.DRIVER_NONE] = 0
        self.listenerStats[ListenerStat.LOGGING_IN] = 0
        self.listenerStats[ListenerStat.PLAYING] = 0

    def getStats(self):
        return {
            'version': VERSION,
            'error': self.listenerStats[ListenerStat.ERROR],
            'driverNone': self.listenerStats[ListenerStat.DRIVER_NONE],
            'played': self.listenerStats[ListenerStat.PLAYED],
            'loggingIn': self.listenerStats[ListenerStat.LOGGING_IN],
            'playing': self.listenerStats[ListenerStat.PLAYING],
            'overriddePlaylist': bool(self.overridePlaylist),
        }
    
    def getConsoleLines(self, width: int, height: int):
        stats = self.listenerStats
        lines = []
        lines.append(Fore.WHITE + 'Logging in: %7d   Playing: %7d   Playedd: %7d   Error: %7d   Driver None: %7d' % 
            (stats[ListenerStat.LOGGING_IN],
            stats[ListenerStat.PLAYING], 
            stats[ListenerStat.PLAYED],
            stats[ListenerStat.ERROR],
            stats[ListenerStat.DRIVER_NONE],
            ) 
        )
        return lines
        

    def notify(self, eventName: str, target, data):
        pass

    def getNewProcess(self, freeSlot: int):
        try:
            self.remoteQueue.provision(freeSlot)
            message = self.remoteQueue.pop()
            
            if message:
                body = loads(message['Body'])
                
                if self.overridePlaylist:
                    body['playlist'] = self.overridePlaylist

                p = Process(target = runner, kwargs={
                    'console': self.console, 
                    'shutdownEvent': self.shutdownEvent, 
                    'headless': self.headless, 
                    'vnc': self.vnc,
                    'user': body['user'],
                    'proxy': None,
                    'playlist': body['playlist'],
                    'screenshotDir': self.screenshotDir,
                    'stats': self.listenerStats,
                })
                self.remoteQueue.deleteMessage(message)
                
                return p
        except Exception as e:
            self.console.exception()
            self.listenerStats[ListenerStat.ERROR] += 1

class Scenario(AbstractScenario):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        pass

    def start(self):
        logDir = self.userDir + '/listener/' + datetime.now().strftime("%m-%d-%Y-%H-%M-%S")
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
        
        listenerConfig = Config.getListenerConfig(self.configFile, defautlConfig)

        if not listenerConfig:
            sys.exit('I can not continue without configuraton')
        

        #https://sqs.eu-west-3.amazonaws.com/884650520697/18e66ed8d655f1747c9afbc572955f46
        
        if self.args.verbose:
            verbose = 3
        else:
            verbose = 1

        console = Console(verbose=verbose, ouput=self.args.verbose, logfile=logDir + '/session.log', logToFile=not self.args.nolog)

        if not listenerConfig['sqs_endpoint']:
            sys.exit('you need to set the sqs_endpoint in the config file.')

        if not listenerConfig['server_id']:
            sys.exit('you need to set the server_id in the config file.')

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
            queueEndPoint=listenerConfig['sqs_endpoint'],
            shutdownEvent=self.shutdownEvent,
            console= console,
            headless=self.args.headless,
            vnc= self.args.vnc,
            screenshotDir=screenshotDir,
            overridePlaylist=playlist
            )

        pm = ProcessManager(
            statsServer=answers['stats_server'],
            serverId=listenerConfig['server_id'],
            userDir=self.userDir,
            console=console,
            processProvider=pp,
            maxProcess=maxProcess,
            spawnInterval=listenerConfig['spawn_interval'],
            showInfo=not self.args.noinfo,
            shutdownEvent=self.shutdownEvent,
        )

        pm.start()
    